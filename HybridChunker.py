import numpy as np

from typing import List, Dict, Any

from dataclasses import dataclass

import spacy

import torch

from transformers import AutoTokenizer, AutoModel

from sentence_transformers import SentenceTransformer

import faiss

import json

import os



@dataclass

class Document:

    text: str

    metadata: Dict[str, Any] = None



class HybridChunker:

    def __init__(self, language="en_core_web_sm"):

        self.nlp = spacy.load(language)

        

    def _get_semantic_boundaries(self, text: str) -> List[int]:

        """Find semantic boundaries using SpaCy's parser"""

        doc = self.nlp(text)

        boundaries = [0]

        

        for sent in doc.sents:

            # Check for semantic completeness using dependency parsing

            if sent.root.dep_ in ["ROOT"]:

                boundaries.append(sent.end_char)

                

        return boundaries

    

    def chunk_text(self, text: str, max_chunk_size: int = 512, 

                   overlap: int = 50) -> List[Document]:

        """Create chunks using both fixed-size and semantic boundaries"""

        semantic_boundaries = self._get_semantic_boundaries(text)

        chunks = []

        current_pos = 0

        

        while current_pos < len(text):

            # Find the closest semantic boundary within max_chunk_size

            chunk_end = current_pos + max_chunk_size

            best_boundary = chunk_end

            

            for boundary in semantic_boundaries:

                if current_pos < boundary <= chunk_end:

                    best_boundary = boundary

                    

            # Create chunk

            chunk_text = text[current_pos:best_boundary].strip()

            if chunk_text:

                chunks.append(Document(

                    text=chunk_text,

                    metadata={"start": current_pos, "end": best_boundary}

                ))

            

            # Move position considering overlap

            current_pos = best_boundary - overlap

            

        return chunks



class HybridEncoder:

    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2"):

        self.model = SentenceTransformer(model_name)

        

    def encode_documents(self, documents: List[Document]) -> np.ndarray:

        """Encode documents using the SentenceTransformer model"""

        texts = [doc.text for doc in documents]

        embeddings = self.model.encode(texts, convert_to_tensor=True)

        return embeddings.cpu().numpy()



class FAISSIndex:

    def __init__(self, dimension: int, index_type: str = "L2"):

        if index_type == "L2":

            self.index = faiss.IndexFlatL2(dimension)

        elif index_type == "IVF":

            quantizer = faiss.IndexFlatL2(dimension)

            self.index = faiss.IndexIVFFlat(quantizer, dimension, 100)

            

    def add_documents(self, embeddings: np.ndarray):

        """Add document embeddings to the FAISS index"""

        if isinstance(self.index, faiss.IndexIVFFlat) and not self.index.is_trained:

            self.index.train(embeddings)

        self.index.add(embeddings)

        

    def search(self, query_embedding: np.ndarray, k: int = 5) -> tuple:

        """Search for similar documents"""

        distances, indices = self.index.search(query_embedding.reshape(1, -1), k)

        return distances[0], indices[0]

    

    def save(self, filepath: str):

        """Save FAISS index to disk"""

        faiss.write_index(self.index, filepath)

        

    def load(self, filepath: str):

        """Load FAISS index from disk"""

        self.index = faiss.read_index(filepath)



class RAGSystem:

    def __init__(self, chunker: HybridChunker, encoder: HybridEncoder, 

                 dimension: int = 768):

        self.chunker = chunker

        self.encoder = encoder

        self.index = FAISSIndex(dimension)

        self.documents = []

        

    def add_documents(self, texts: List[str]):

        """Process and index new documents"""

        for text in texts:

            # Chunk documents

            chunks = self.chunker.chunk_text(text)

            self.documents.extend(chunks)

            

            # Encode chunks

            embeddings = self.encoder.encode_documents(chunks)

            

            # Add to index

            self.index.add_documents(embeddings)

    

    def search(self, query: str, k: int = 5) -> List[Document]:

        """Search for relevant documents"""

        # Encode query

        query_embedding = self.encoder.encode_documents([Document(text=query)])[0]

        

        # Search index

        distances, indices = self.index.search(query_embedding, k)

        

        # Return matched documents

        return [self.documents[idx] for idx in indices]

    

    def save(self, directory: str):

        """Save the entire RAG system"""

        os.makedirs(directory, exist_ok=True)

        

        # Save FAISS index

        self.index.save(os.path.join(directory, "index.faiss"))

        

        # Save documents

        documents_data = [

            {"text": doc.text, "metadata": doc.metadata}

            for doc in self.documents

        ]

        with open(os.path.join(directory, "documents.json"), "w") as f:

            json.dump(documents_data, f)

    

    def load(self, directory: str):

        """Load the entire RAG system"""

        # Load FAISS index

        self.index.load(os.path.join(directory, "index.faiss"))

        

        # Load documents

        with open(os.path.join(directory, "documents.json"), "r") as f:

            documents_data = json.load(f)

            self.documents = [

                Document(text=doc["text"], metadata=doc["metadata"])

                for doc in documents_data

            ]



# Example usage

if __name__ == "__main__":

    # Initialize system

    chunker = HybridChunker()

    encoder = HybridEncoder()

    rag_system = RAGSystem(chunker, encoder)

    

    # Add documents

    documents = [

        "This is a sample document. It contains multiple sentences with semantic meaning.",

        "Another document with different content. This shows how the system works."

    ]

    rag_system.add_documents(documents)

    

    # Search

    results = rag_system.search("sample sentences", k=2)

    

    # Save system

    rag_system.save("rag_system")

    

    # Load system

    new_rag_system = RAGSystem(chunker, encoder)

    new_rag_system.load("rag_system")
