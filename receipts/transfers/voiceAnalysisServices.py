import speech_recognition as sr
import streamlit as st
from transformers import pipeline
from textblob import TextBlob
import pandas as pd
import gc
import flair
from loadModules import LoadModules

# import gradio as gr
# import whisper

# Twitter-roberta-base-sentiment is a roBERTa model trained on ~58M tweets and fine-tuned for sentiment analysis. Fine-tuning is the process of taking a pre-trained large language model (e.g. roBERTa in this case) and then tweaking it with additional training data to make it perform a second similar task (e.g. sentiment analysis).
# Bert-base-multilingual-uncased-sentiment is a model fine-tuned for sentiment analysis on product reviews in six languages: English, Dutch, German, French, Spanish and Italian.
# Distilbert-base-uncased-emotion is a model fine-tuned for detecting emotions in texts, including sadness, joy, love, anger, fear and surprise.
# DistilBERT is a smaller, faster and cheaper version of BERT. It has 40% smaller than BERT and runs 60% faster while preserving over 95% of BERT’s performance.
# bhadresh-savani/bert-base-uncased-emotion gives better all emotions levels

distilbert_base_uncased_model = "distilbert-base-uncased-finetuned-sst-2-english"
bhadresh_savani_bert_base_uncased_emotion_model = "bhadresh-savani/bert-base-uncased-emotion"


class VoiceAnalysisServices(LoadModules):
    load_Modules = LoadModules(False)

    def __init__(self):
        print('in VoiceAnalysisServices constructor')
        if (self.load_Modules == None):
            self.load_Modules = LoadModules(False)

    def perform_sentiment_analysis(self, text, return_all, model, isFileUpload=False):
        if 'current_model' not in st.session_state:
            print(f'Setting the current_model as {model}')
            st.session_state['current_model'] = model
        print(f' Model parameter is {model}')
        if model == 'distilbert':
            st.session_state['current_model'] = model
            print(f' Using Model {model}')
            return self.perform_sentiment_analysis_using_distilbert(text, return_all)
        elif model == 'vader':
            st.session_state['current_model'] = model
            print(f' Using Model {model}')
            return self.perform_sentiment_analysis_using_vader(text)
        elif model == 'roberta':
            st.session_state['current_model'] = model
            print(f' Using Model {model}')
            # set to all to get all emotions
            return_all = True
            return self.perform_sentiment_analysis_using_sam_lowe(text, return_all)
        elif model == 'flair':
            print(f' Using Model {model}')
            st.session_state['current_model'] = model
            return self.perform_sentiment_analysis_using_flair(text, return_all)
        elif model == 'savani':
            print(f' Using Model {model}')
            st.session_state['current_model'] = model
            if type(text) != str:
                return self.perform_text_classification_using_bhadresh_savani(text, return_all)
            else:
                return self.perform_text_classification_using_old_bhadresh_savani(text, False)
        elif model == 'textblob':
            print(f' Using Model {model}')
            st.session_state['current_model'] = model
            return self.perform_sentiment_analysis_using_textblob(text)
        elif model == 'All':
            print(f' Using Model {model}')
            st.session_state['current_model'] = model
            print(f' Using Model {model}')
            return self.perform_sentiment_analysis_all(text)
        else:
            return self.perform_sentiment_analysis_using_flair(text, return_all)

    def perform_sentiment_analysis_using_flair(self, text, return_all):
        try:
            flair_sentiment = None
            if LoadModules.all_modules and 'flair' in LoadModules.all_modules.keys():
                print('Found flair_sentiment in LoadModules.all_modules')
                flair_sentiment = LoadModules.all_modules['flair']
            else:
                print('Not found flair_sentiment LoadModules.all_modules, loading...')
                flair_sentiment = self.load_Modules.load_model_flair()
                # print(LoadModules.all_modules.keys())
            # download mode
            # flair_sentiment = flair.models.TextClassifier.load('en-sentiment')
            s = flair.data.Sentence(text)
            flair_sentiment.predict(s)
            # print(s.score)
            # print(s.get_label().value)
            total_sentiment = s.labels
            model = st.session_state['current_model']
            # print(f'Sentiment analysis {model} results are {total_sentiment}')
            if return_all:
                return s
            else:
                if s:
                    sentiment_label = s.get_label().value
                    sentiment_score = s.score
                    sign = 1 if sentiment_label == 'POSITIVE' else -1
                    sentiment_score = sentiment_score * sign
                    return sentiment_label, sentiment_score
                else:
                    return 'bad_data', 'Not Enough or Bad Data'
        except Exception as ex:
            print("Error occurred during .. perform_sentiment_analysis_using_flair")
            print(str(ex))
            return "error", str(ex)

    def perform_sentiment_analysis_all(self, text):
        print('In perform_sentiment_analysis_all')
        sentiment_and_scores = dict()
        sentiment_label, sentiment_score = self.perform_sentiment_analysis_using_textblob(text)
        sentiment_and_scores['textblob'] = {'sentiment_label': sentiment_label, 'sentiment_score': sentiment_score}
        sentiment_label, sentiment_score = self.perform_sentiment_analysis_using_flair(text, False)
        sentiment_and_scores['flair'] = {'sentiment_label': sentiment_label, 'sentiment_score': sentiment_score}
        sentiment_label, sentiment_score = self.perform_sentiment_analysis_using_vader(text)
        sentiment_and_scores['vader'] = {'sentiment_label': sentiment_label, 'sentiment_score': sentiment_score}
        sentiment_label, sentiment_score = self.perform_sentiment_analysis_using_sam_lowe(text, False)
        sentiment_and_scores['roberta'] = {'sentiment_label': sentiment_label, 'sentiment_score': sentiment_score}
        sentiment_label, sentiment_score = self.perform_sentiment_analysis_using_distilbert(text, False)
        sentiment_and_scores['distilbert'] = {'sentiment_label': sentiment_label, 'sentiment_score': sentiment_score}
        return sentiment_and_scores

    def perform_sentiment_analysis_using_textblob(self, text):
        try:
            print('Nothing to Load for textBlob')
            sentiment_label, sentiment_score = self.text_blob_sentiments(text)
            print(f'Sentiment analysis [TextBlob] results are {sentiment_label} ({sentiment_score})')
            return sentiment_label, sentiment_score
        except Exception as ex:
            print("Error occurred during .. perform_sentiment_analysis_using_textblob")
            print(str(ex))
            return "error", str(ex)

    def perform_sentiment_analysis_using_distilbert(self, text, return_all):
        current_model = st.session_state['current_model']
        try:
            if LoadModules.all_modules and 'distilbert' in LoadModules.all_modules.keys():
                print('Found distilbert_sentiment_analysis in global')
                distilbert_sentiment_analysis = LoadModules.all_modules['distilbert']
            else:
                print('Not found distilbert_sentiment_analysis global, loading...')
                distilbert_sentiment_analysis = self.load_Modules.load_model_distilbert()
            # model_name = "distilbert-base-uncased-finetuned-sst-2-english"
            # sentiment_analysis = pipeline("sentiment-analysis", model=model_name, return_all_scores=return_all)
            results = distilbert_sentiment_analysis(text)
            print(f'Sentiment analysis {current_model} results are {results}')
            if return_all:
                return results[0]
            else:
                if (results[0] and results[0][0]):
                    print(results[0][0])
                    sentiment_label = results[0][0]['label']
                    sentiment_score = results[0][0]['score']
                    sign = 1 if sentiment_label == 'POSITIVE' else -1
                    sentiment_score = sentiment_score * sign
                    return sentiment_label, sentiment_score
                else:
                    return 'bad_data', 'Not Enough or Bad Data'
        except Exception as ex:
            print("Error occurred during .. perform_sentiment_analysis_using_distilbert")
            print(str(ex))
            return "error", str(ex)

    # Text Classification input text has to be in the dataframe
    def perform_text_classification_using_bhadresh_savani(self, text_in_a_dataframe, return_all):
        # model_name = "bhadresh-savani/bert-base-uncased-emotion"
        # savani_classification = pipeline("text-classification", model=model_name, return_all_scores=return_all)
        if LoadModules.all_modules and 'savani' in LoadModules.all_modules.keys():
            print('Found savani_classification in LoadModules.all_modules')
            savani_classification = LoadModules.all_modules['savani']
        else:
            print('Not found savani_classification LoadModules.all_modules, loading')
            savani_classification = self.load_Modules.load_model_bhadresh_savani()

        text_in_a_dataframe['result'] = text_in_a_dataframe["text"].apply(savani_classification)
        text_in_a_dataframe['result'] = text_in_a_dataframe['result'].apply(lambda x: x[0])
        text_in_a_dataframe[['label', 'score']] = text_in_a_dataframe['result'].apply(pd.Series)
        text_in_a_dataframe['result'].apply(pd.Series)
        text_in_a_dataframe.drop('result', axis=1, inplace=True)
        # text_in_a_dataframe.rename(columns={'label':'sentiment'},inplace=True)
        # text_in_a_dataframe.rename(columns={'score': 'polarity'},inplace=True)

        result = pd.DataFrame()
        result['sentiment'] = text_in_a_dataframe['label']
        result['polarity'] = text_in_a_dataframe['score']
        print(f'Text Classification Analysis results are {result.sample()}')
        # if return_all:
        del text_in_a_dataframe
        gc.collect()

        return result

    # Text Classification
    def perform_text_classification_using_old_bhadresh_savani(self, text, return_all):
        # model_name = "bhadresh-savani/bert-base-uncased-emotion"
        # savani_classification = pipeline("text-classification", model=model_name, return_all_scores=return_all)
        if LoadModules.all_modules and 'savani' in LoadModules.all_modules.keys():
            print('Found savani_classification in LoadModules.all_modules')
            savani_classification = LoadModules.all_modules['savani']
        else:
            print('Not found savani_classification LoadModules.all_modules, loading')
            savani_classification = self.load_Modules.load_model_bhadresh_savani()

        results = savani_classification(text)
        print(f'Text Classification Analysis results are {results}')
        if return_all:
            return results[0]
        else:
            if results[0]:
                # print(results[0])
                sentiment_label = results[0]['label']
                sentiment_score = results[0]['score']
                return sentiment_label, sentiment_score
            else:
                return 'bad_data', 'Not Enough or Bad Data'

    def perform_sentiment_analysis_using_sam_lowe(self, text, return_all):
        current_model = st.session_state['current_model']
        sam_lowe_classification = None
        if LoadModules.all_modules and 'sam_lowe' in LoadModules.all_modules.keys():
            print('Found sam_lowe_classification in global')
            sam_lowe_classification = LoadModules.all_modules['savani']
        else:
            print('Not found sam_lowe_classification global, loading...')
            sam_lowe_classification = self.load_Modules.load_model_sam_lowe(False)

        results = sam_lowe_classification(text)
        print(f'Sentimental Analysis  {current_model} results are {results}')
        if return_all:
            return results[0]
        else:
            sentiment_label = results[0]['label']
            sentiment_score = results[0]['score']
            return sentiment_label, sentiment_score

    def transcribe_audio_file(self, audio_file):
        with sr.WavFile(audio_file) as source:
            r = sr.Recognizer()
            audio = r.record(source)
            try:
                transcribed_text1 = r.recognize_google(audio)
                print(r.recognize_google(audio, language='en-US'))
            except sr.UnknownValueError:
                print("Google could not understand audio")
            except sr.RequestError as e:
                print("Google error; {0}".format(e))
            return transcribed_text1

    def transcribe_audio_data(self, audio_data):
        try:
            r = sr.Recognizer()
            transcribed_text1 = r.recognize_google(audio_data)
            print(r.recognize_google(audio_data, language='en-US'))
        except sr.UnknownValueError:
            print("Google could not understand audio")
        except sr.RequestError as e:
            print("Google error; {0}".format(e))
        return transcribed_text1

    def text_blob_sentiments(self, text):
        # Create a TextBlob object
        try:
            output = TextBlob(text)
            if output:
                polarity = output.sentiment.polarity
                subjectivity = output.subjectivity
                if -0.02 > polarity and subjectivity > 0:
                    return 'NEGATIVE', polarity
                elif -0.02 <= polarity <= 0.02:
                    return 'NEUTRAL', polarity
                else:
                    return 'POSITIVE', polarity
        except Exception as ex:
            print("Error occurred during .. text_blob_sentiments")
            print(str(ex))
            return "error", str(ex)

    # def text_blob_sentimentsOnly(self, text):
    #     # Create a TextBlob object
    #     try:
    #         output = TextBlob(text)
    #         if output:
    #             polarity = output.sentiment.polarity
    #             subjectivity = output.subjectivity
    #             # print(text, polarity, subjectivity)
    #             if -0.02 > polarity and subjectivity > 0:
    #                 return 'NEGATIVE'
    #             elif -0.2 < polarity < 0.2:
    #                 return 'NEUTRAL'
    #             elif polarity > 0.02:
    #                 return 'POSITIVE'
    #     except Exception as ex:
    #         print("Error occurred during .. text_blob_sentiments")
    #         print(str(ex))
    #         return "error", str(ex)
    #
    # def text_blob_polarityOnly(self, text):
    #     # Create a TextBlob object
    #     try:
    #         output = TextBlob(text)
    #         if output:
    #             polarity = output.sentiment.polarity
    #             # subjectivity = output.subjectivity
    #             # print(polarity, subjectivity)
    #             # if -0.02 > polarity and subjectivity > 0:
    #             #     return 'NEGATIVE'
    #             # elif -0.2 < polarity < 0.2:
    #             #     return 'NEUTRAL'
    #             # elif polarity > 0.02:
    #             #     return 'POSITIVE'
    #             return polarity
    #     except Exception as ex:
    #         print("Error occurred during .. text_blob_sentiments")
    #         print(str(ex))
    #         return "error", str(ex)

    def analyze_sentiment(self, text):
        sentiment_analysis = pipeline("sentiment-analysis", framework="pt", model="SamLowe/roberta-base-go_emotions")
        results = sentiment_analysis(text)
        sentiment_results = {result['label']: result['score'] for result in results}
        return sentiment_results

    # def inference(audio, sentiment_option):
    #     model = whisper.load_model("base")
    #
    #     audio = whisper.load_audio(audio)
    #     audio = whisper.pad_or_trim(audio)
    #
    #     mel = whisper.log_mel_spectrogram(audio).to(model.device)
    #
    #     _, probs = model.detect_language(mel)
    #     lang = max(probs, key=probs.get)
    #
    #     options = whisper.DecodingOptions(fp16=False)
    #     result = whisper.decode(model, mel, options)
    #
    #     sentiment_results = analyze_sentiment(result.text)
    #     return sentiment_results
    #
    #     sentiment_output = display_sentiment_results(sentiment_results, sentiment_option)
    #
    #     return lang.upper(), result.text, sentiment_output

    # function to print sentiments
    # of the sentence.
    def perform_sentiment_analysis_using_vader(self, sentence):
        current_model = st.session_state['current_model']
        vader_obj = None
        if LoadModules.all_modules and 'vader' in LoadModules.all_modules.keys():
            print('Found vader_obj in LoadModules.all_modules')
            vader_obj = LoadModules.all_modules['vader']
        else:
            print('Not found vader_obj global, loading...')
            vader_obj = self.load_Modules.load_model_vader()

        # polarity_scores method of SentimentIntensityAnalyzer
        # object gives a sentiment dictionary.
        # which contains pos, neg, neu, and compound scores.
        sentiment_dict = vader_obj.polarity_scores(sentence)
        print(f'Semtiment Analysis  {current_model} results are {sentiment_dict}')
        if sentiment_dict:
            # decide sentiment as positive, negative and neutral
            if sentiment_dict['compound'] >= 0.05:
                sentiment_label = 'Positive'
                sentiment_score = sentiment_dict['pos']
            elif sentiment_dict['compound'] <= - 0.05:
                sentiment_label = 'Negative'
                sentiment_score = sentiment_dict['neg']
            else:
                sentiment_label = 'Neutral'
                sentiment_score = sentiment_dict['neu']
            return sentiment_label, sentiment_score
        else:
            return 'bad_data', 'Bad Data or Insufficient Data'
