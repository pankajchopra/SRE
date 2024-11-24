import time
import traceback
import pandas as pd
from data_cache import pandas_cache
import streamlit as st
from voiceAnalysisServices import VoiceAnalysisServices
from myUtilityDefs import convert_to_new_dictionary, print_sentiments, get_sentiment_emoji
from os import path
import audio_recorder_streamlit as ars
import matplotlib.pyplot as plt
import numpy as np
import nltk

nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('wordnet')
nltk.download('vader_lexicon')
# nltk.download('all-corpora')


voiceAnalysisServices = VoiceAnalysisServices()
st.set_page_config(layout="wide")

# print("Setting session state")
actionRadioButtonState = st.session_state.get("enable_radio", {"value": True})
uploadButtonState = st.session_state.get("enable_upload", {"value": True})
st.markdown(' # FA/Client Sentiment Analysis!')
# footer = st.footer('Author: *Pankaj Kumar Chopra*')
# st.markdown(
#     """
#     <style>
#     #MainMenu {visibility: hidden;}
#     footer {visibility: visible;}
#     </style>
#     """,
#     unsafe_allow_html=True
# )
# st.image('work-in-progress.png', width=100)
with st.sidebar:
    st.title("Audio Analysis")
    st.markdown("_last deploy: 7/27/2022_")
    st.write("""The Audio Analysis app is a powerful tool that allows you to analyze audio files 
                     and gain valuable insights from them. It combines speech recognition 
                     and sentiment analysis techniques to transcribe the audio 
                     and determine the sentiment expressed within it.""")
    sentiment_models = {
        'TextBlob(PatternAnlyzer) Based Sentiment Analysis': "textblob",
        # 'TextBlob(NaiveBayesAnlyzer) Based Sentiment Analysis': "textblob",
        'VADER Based Sentiment Analysis': 'vader',
        'FLAIR Based Sentiment Analysis': 'flair',
        'Distilbert-Sentiment Analysis': 'distilbert',
        'SamLowe/RoBERTa-base-go_emotions': 'samLowe',
        'Text Classification-Bhadresh-Savani': 'savani',
        'Question-Answering':'deepset',
        "Compare-TextBlob-Vader-Flair-Distilbert": 'All',
        # "Compare-Savani & SamLowe": 'All-SS'
    }
    model_select = st.selectbox(
        "Select the model to predict : ", list(sentiment_models.keys()))
    model_predict = sentiment_models.get(model_select)

    action_names = ['Sample Audio', 'Upload an Audio', 'Live Audio', 'Plain Text', 'Upload a file(text in each line)']
    action = st.radio('Actions',
                              action_names,
                              key='action_radio',
                              disabled= not actionRadioButtonState
                              )


def write_current_status(status_area, text):
    if not status_area:
        status_area = st.write("")
    with status_area:
        st.empty()
        st.markdown('**'+text+'**')


def display_all_results_for_multiple_senetence(model, return_all, transcribed_text):
    st.write('''Text Classification Analysis Emotions comparison for roBERTa and SamLowe Text Classification models
                        [Click Here](https://aashishmehta.com/sentiment-analysis-comparison/)''')
    result = voiceAnalysisServices.perform_sentiment_analysis(transcribed_text, return_all, model)
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    # print(result)
    # st.write(result)
    mystyle = '''
                <style>
                    p {
                        text-align: justify;
                    }
                </style>
                '''
    st.markdown(mystyle, unsafe_allow_html=True)
    for k in list(result.keys()):
        sentiment_label = result.get(k)['sentiment_label']
        sentiment_score = result.get(k)['sentiment_score']
        if k == 'flair':
            col1.markdown("<font size='5' align='center'> Model: {} </font>".format(k.upper()), unsafe_allow_html=True)
            col1.markdown("<font size='4' > Score: {} </font>".format(sentiment_score), unsafe_allow_html=True)
            col1.subheader(f"{get_sentiment_emoji(sentiment_label.lower())} {sentiment_label}")
            col1.info("""Flair, employs pre-trained language models and transfer 
                    learning to generate contextual string embeddings 
                    for sentiment analysis""")
        if k == 'vader':
            col2.markdown("<font size='5' align='center'> Model: {} </font>".format(k.upper()), unsafe_allow_html=True)
            col2.markdown("<font size='4' > Score: {} </font>".format(sentiment_score), unsafe_allow_html=True)
            col2.subheader(f"{get_sentiment_emoji(sentiment_label.lower())} {sentiment_label}")
            col2.info("""VADER (Valence Aware Dictionary 
                               and sEntiment Reasoner) is a rule-based model that uses a 
                               sentiment lexicon and grammatical rules to determine 
                               the sentiment scores of the text. """)
        if k == 'textblob':
            col3.markdown("<font size='5' align='center'> Model: {} </font>".format(k.upper()), unsafe_allow_html=True)
            col3.markdown("<font size='4' > Score: {} </font>".format(sentiment_score), unsafe_allow_html=True)
            col3.subheader(f"{get_sentiment_emoji(sentiment_label.lower())} {sentiment_label}")
            col3.info("""TextBlob(default PatternAnalyzer) is a Python NLP library that uses a natural language toolkit (NLTK).  
                                               aTextblob it gives two outputs, which are polarity and subjectivity. 
                                               Polarity is the output that lies between [-1,1], where -1 refers to negative 
                                               sentiment and +1 refers to positive sentiment. Subjectivity is the output that 
                                               lies within [0,1] and refers to personal opinions and judgments 
                                               sentiment lexicon and grammatical rules to determine 
                                               the sentiment scores of the text. More details here[PatternAnalysis](https://phdservices.org/pattern-analysis-in-machine-learning/) [Naive Bayes](https://www.machinelearningplus.com/predictive-modeling/how-naive-bayes-algorithm-works-with-example-and-full-code/)""")


def process_and_show_sentimental_analysis_results(audio_file, transcribed, transcribed_text, model):
    if not transcribed and audio_file:
        st.write(f'Processing {audio_file}...' )
        transcribed_text = voiceAnalysisServices.transcribe_audio_file(audio_file)
        # st.header("Transcribed Text")
        st.text_area("Transcribed Text", transcribed_text, key=1, height=150)
    else:
        # st.header("Text")
        st.text_area("Text", transcribed_text, height=150)
    # st.markdown(" # Analysing...")
    return_all = False
    if model == 'All':
        if not isinstance(transcribed_text, str):
            display_all_results_for_multiple_senetence(model, return_all, transcribed_text)
        else: #'All-SS'
            display_all_results_for_one_senetence(model, return_all, transcribed_text)
    else:
        print(f'model is {model}')
        sentiment_label, sentiment_score = voiceAnalysisServices.perform_sentiment_analysis(transcribed_text, return_all, model)
        if(sentiment_label == 'error'):
            traceback.print_exc()
        else:
            st.header(f"Sentiment Analysis  ")
            st.markdown("<font size='5'>  Model: {} </font>".format( model_select), unsafe_allow_html=True)
            st.markdown("*" + print_sentiments(sentiment_label, sentiment_score) + "*")


def process_and_show_new_sentimental_analysis_results(audio_file, transcribed, transcribed_text, model):
    if not transcribed and audio_file:
        st.write(f'Processing {audio_file}...' )
        transcribed_text = voiceAnalysisServices.transcribe_audio_file(audio_file)
        # st.header("Transcribed Text")
        st.text_area("Transcribed Text", transcribed_text, key=1, height=150)
    else:
        # st.header("Text")
        st.text_area("Text", transcribed_text, height=150)
    # st.markdown(" # Analysing...")
    return_all = False
    if 'All' in model:
        if not isinstance(transcribed_text, str):
            display_all_results_for_one_senetence(model, return_all, transcribed_text)
    else: # Not all but any if the other
        print(f'model is {model}')
        result = voiceAnalysisServices.perform_sentiment_analysis(transcribed_text, return_all, model)
        if len(result) == 1:
            sentiment = result['sentiment'][0]
            score = result['polarity'][0]
            st.markdown("*" + print_sentiments(sentiment, score) + "*")
            if sentiment == 'error':
                traceback.print_exc()
            else:
                st.header(f"Sentiment Analysis  ")
                st.markdown("<font size='5'>  Model: {} </font>".format( model_select), unsafe_allow_html=True)
                st.markdown("*" + print_sentiments(sentiment, score) + "*")


def display_all_results_for_one_senetence(model, return_all, transcribed_text):
    st.write('''Sentiment analysis comparison for three NLP tools
                    Vader vs Flair vs TextBlob [Click Here](https://aashishmehta.com/sentiment-analysis-comparison/)''')
    result = voiceAnalysisServices.perform_sentiment_analysis(transcribed_text, return_all, model)
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    # print(result)
    # st.write(result)
    mystyle = '''
            <style>
                p {
                    text-align: justify;
                }
            </style>
            '''
    st.markdown(mystyle, unsafe_allow_html=True)
    for k in list(result.keys()):
        sentiment_label = result.get(k)['sentiment_label']
        sentiment_score = result.get(k)['sentiment_score']
        if k == 'flair':
            col1.markdown("<font size='5' align='center'> Model: {} </font>".format(k.upper()), unsafe_allow_html=True)
            col1.markdown("<font size='4' > Score: {} </font>".format(sentiment_score), unsafe_allow_html=True)
            col1.subheader(f"{get_sentiment_emoji(sentiment_label.lower())} {sentiment_label}")
            col1.info("""Flair, employs pre-trained language models and transfer 
                learning to generate contextual string embeddings 
                for sentiment analysis""")
        if k == 'vader':
            col2.markdown("<font size='5' align='center'> Model: {} </font>".format(k.upper()), unsafe_allow_html=True)
            col2.markdown("<font size='4' > Score: {} </font>".format(sentiment_score), unsafe_allow_html=True)
            col2.subheader(f"{get_sentiment_emoji(sentiment_label.lower())} {sentiment_label}")
            col2.info("""VADER (Valence Aware Dictionary 
                           and sEntiment Reasoner) is a rule-based model that uses a 
                           sentiment lexicon and grammatical rules to determine 
                           the sentiment scores of the text. """)
        if k == 'textblob':
            col3.markdown("<font size='5' align='center'> Model: {} </font>".format(k.upper()), unsafe_allow_html=True)
            col3.markdown("<font size='4' > Score: {} </font>".format(sentiment_score), unsafe_allow_html=True)
            col3.subheader(f"{get_sentiment_emoji(sentiment_label.lower())} {sentiment_label}")
            col3.info("""TextBlob(default PatternAnalyzer) is a Python NLP library that uses a natural language toolkit (NLTK).  
                                           aTextblob it gives two outputs, which are polarity and subjectivity. 
                                           Polarity is the output that lies between [-1,1], where -1 refers to negative 
                                           sentiment and +1 refers to positive sentiment. Subjectivity is the output that 
                                           lies within [0,1] and refers to personal opinions and judgments 
                                           sentiment lexicon and grammatical rules to determine 
                                           the sentiment scores of the text. More details here[PatternAnalysis](https://phdservices.org/pattern-analysis-in-machine-learning/) [Naive Bayes](https://www.machinelearningplus.com/predictive-modeling/how-naive-bayes-algorithm-works-with-example-and-full-code/)""")
        # if k == 'roberta':
        #     col4.markdown("<font size='5' align='center'> Model: {} </font>".format(k.upper()), unsafe_allow_html=True)
        #     col4.markdown("<font size='4' > Score: {} </font>".format(sentiment_score), unsafe_allow_html=True)
        #     col4.subheader(f"{get_sentiment_emoji(sentiment_label.lower())} {sentiment_label}")
        #     col4.info("""Twitter-roberta-base-sentiment is a roBERTa model trained
        #         on ~58M tweets and fine-tuned for sentiment analysis.
        #         Fine-tuning is the process of taking a pre-trained
        #          large language model (e.g. roBERTa in this case)
        #          and then tweaking it with additional training
        #         data to make it perform a second similar task (e.g. sentiment analysis""")
        if k == 'distilbert':
            col4.markdown("<font size='5' align='center'> Model: {} </font>".format(k.upper()), unsafe_allow_html=True)
            col4.markdown("<font size='4' > Score: {} </font>".format(sentiment_score), unsafe_allow_html=True)
            col4.subheader(f"{get_sentiment_emoji(sentiment_label.lower())} {sentiment_label}")
            col4.info("""DistilBERT is a smaller, faster and cheaper version of BERT. 
                It has 40% smaller than BERT 
                and runs 60% faster while preserving over 95% of BERT’s performance""")


def process_and_show_text_classification_results(audio_file, transcribed, transcribed_text):
    if not transcribed:
        st.write(f'Processing {audio_file}...' )
        transcribed_text = pd.DataFrame({"text":[voiceAnalysisServices.transcribe_audio_file(audio_file)]})
        st.text_area("Transcribed Text", transcribed_text, key=2, height=200)

    st.header("Text Classification Results Analysis(Bert-base-uncased-emotion)")
    result = voiceAnalysisServices.perform_text_classification_using_bhadresh_savani(pd.DataFrame({"text":[transcribed_text]}), return_all=False)
    if len(result) == 1:
        sentiment = result['sentiment'][0]
        score = result['polarity'][0]
        st.markdown("*"+print_sentiments(sentiment, score)+ "*")


def process_and_plot_text_classification_results(audio_file, transcribed, transcribed_text, return_all):
    if not transcribed:
        st.write(f'Processing {audio_file}...' )
        tt = voiceAnalysisServices.transcribe_audio_file(audio_file)
        transcribed_text = pd.DataFrame({"text": [tt]})

        # st.header("Transcribed Text")
        st.text_area("Transcribed Text", transcribed_text, key=2, height=200)

    # st.markdown(" # Text Classification...")
    st.header("Text Classification Results Analysis(Bert-base-uncased-emotion)")
    if return_all:
        resultDict = voiceAnalysisServices.perform_text_classification_using_bhadresh_savani(transcribed_text, return_all)
        rsultDictionary=convert_to_new_dictionary(resultDict)
        plot_to_charts(resultDict)
        # sentimental_results = []
        # for key, value in rsultDictionary.items():
        #     sentimental_results.append(f'{key}({value}) ')
        #
        # st.markdown("*"+''.join(sentimental_results)+ "*")
    else:
        sentiment_label, sentiment_score = voiceAnalysisServices.perform_text_classification_using_bhadresh_savani(transcribed_text, return_all)
        st.markdown("*"+print_sentiments(sentiment_label, sentiment_score)+ "*")


def display_sentiment_results(sentiment_results, option):
    sentiment_text = ""
    for sentiment, score in sentiment_results.items():
        emoji = get_sentiment_emoji(sentiment)
        if option == "Sentiment Only":
            sentiment_text += f"{sentiment} {emoji}\n"
        elif option == "Sentiment + Score":
            sentiment_text += f"{sentiment} {emoji}: {score}\n"
    return sentiment_text


def doActualthings(status_area,audio_file, model):
    with st.spinner('Processing...'):
        progressBar = st.progress(5,"Processing...")
        time.sleep(0.2)
        progressBar.progress(15, 'Transcribing...')

        # write_current_status(main_status, f'   *Selected Sample File: {audio_file}*')
        write_current_status(status_area, f'Transcribing audio of  {audio_file}...')
        transcribed_text = voiceAnalysisServices.transcribe_audio_file(audio_file)
        progressBar.progress(40, 'Semantic Analysis..')
        write_current_status(status_area, f'''Semantic Analysis using {model_predict} 
                                            File Name: {audio_file}...''')
        process_and_show_sentimental_analysis_results(None, True, transcribed_text, model)

        if model_predict != 'All'  and model_predict != 'savani':
            progressBar.progress(70, 'Textual Classification..')
            write_current_status(status_area, f'Text Classification of {audio_file}...')
            process_and_show_text_classification_results(audio_file, True, transcribed_text)
            progressBar.progress(90, 'Textual Classification Done...')
        # write_current_status(status_area, 'Finished Processing!! ')
        progressBar.progress(100, 'Done, Finished Processing!!')


def main():
    # progress_bar = st.progress(0)
    # st.session_state['progress_bar'] = progress_bar
    status_area = st.markdown('')
    if action in 'Sample Audio':
        with st.sidebar:
            process_sample1_button = st.button("Sample 1 ( Last Live Audio)", key=1)
            process_sample2_button = st.button("Call Center Sample", key=2)
            process_sample3_button = st.button("Sample 3", key=3)
            # col1, col2 = st.columns([1, 2])
            # col1.markdown("**Upload an audio file (format = wav only) **")
            # col2.markdown("*Do not upload music wav file it will give error(s).*")
        audio_file1 = path.join(path.dirname(path.realpath(__file__)), "recorded.mp3")
        audio_file2 = path.join(path.dirname(path.realpath(__file__)), "voices/call_center.wav")
        audio_file3 = path.join(path.dirname(path.realpath(__file__)), "voices/OSR_us_000_0019_8k.wav")
        try:
            if process_sample1_button:
                doActualthings( status_area, audio_file1, model_predict)
            elif process_sample2_button:
                # actionRadioButtonState["value"] = False
                # st.session_state.actionRadioButtonState = actionRadioButtonState
                doActualthings(status_area,audio_file2, model_predict)
            elif process_sample3_button:
                # actionRadioButtonState["value"] = False
                # st.session_state.actionRadioButtonState = actionRadioButtonState
                doActualthings(status_area, audio_file3, model_predict)
        except Exception as ex:
            st.error("Error occurred during audio transcription and sentiment analysis.")
            st.error(str(ex))
            traceback.print_exc()
        finally:
            actionRadioButtonState["value"] = True
            st.session_state.actionRadioButtonState = actionRadioButtonState
    elif action in 'Upload an Audio':
        with st.sidebar:
            audio_file = st.file_uploader("Browse", type=["wav"])
            upload_button = st.button("Upload & Process", key="upload", disabled=not uploadButtonState)
        if audio_file and upload_button:
            try:
                # uploadButtonState["value"] = False
                # st.session_state.uploadButtonState = uploadButtonState
                doActualthings(status_area, audio_file, model_predict)
            except Exception as ex:
                st.error("Error occurred during audio transcription and sentiment analysis.")
                st.error(str(ex))
                traceback.print_exc()
            finally:
                uploadButtonState["value"] = True
                st.session_state.uploadButtonState = uploadButtonState
        # Perform audio tr
    elif action in 'Live Audio':
        with st.sidebar:
            st.markdown('*Audio Recorder*')
            recorded_audio_in_bytes = ars.audio_recorder(text="Click to Record", pause_threshold=3.0, sample_rate=41_000)
        try:
            if recorded_audio_in_bytes is not None:
                if len(recorded_audio_in_bytes) > 0:
                    # convert to a wav file
                    wav_file = open("recorded.mp3", "wb")
                    wav_file.truncate()
                    wav_file.write(recorded_audio_in_bytes)
                    wav_file.close()
                    doActualthings(status_area, "recorded.mp3", model_predict)
        except Exception as ex:
            st.error("Error occurred during audio transcription and sentiment analysis.")
            st.error(str(ex))
            traceback.print_exc()
        finally:
            uploadButtonState["value"] = True
            st.session_state.uploadButtonState = uploadButtonState
    elif action in 'Plain Text':
        with st.sidebar:
            st.markdown('*Plain Text*')
            text = st.text_area('Type or paste few sentences to Analyse(>10 char)', key=9, height=100)
            analyse = st.button('Analyse')
        if analyse and len(text)>10:
            print(f'model_predict is {model_predict} {model_select}')
            # st.header("Seman Classification Results Analysis(Bert-base-uncased-emotion)")
            process_and_show_sentimental_analysis_results(None, True, text, model_predict)
            # print(f'model_predict:{model_predict}')
            if model_predict != 'All' and model_predict != 'savani':
                process_and_show_text_classification_results(None, True, text)
    elif action in 'deepset':

    elif action in 'Upload a file(text in each line)':
        st.markdown('*Upload a Text/csv File (text in each line)*')
        text_csv_file = st.sidebar.file_uploader("Browse", type=["txt", "csv"])
        if model_predict != 'All':
            upload_button_csv_file = st.sidebar.button("Upload & Process", key="uploadcsv")
            if text_csv_file and (text_csv_file.type == 'text/csv' or text_csv_file.type == 'text/plain') and upload_button_csv_file:
                try:
                    with st.spinner('Processing...'):
                        # print('Reading the file')
                        progress_bar = st.progress(5, "Reading the file...")
                        time.sleep(2.0)
                        progress_bar.progress(15, 'Analysing the file...')
                        df = read_the_csv_txt_file(text_csv_file)
                        df.columns = ["text" ]
                        df1 = df.apply(lambda x: x.str.strip())
                        sentiments = list()
                        polarity = list()
                        progress_bar.progress(30, 'Sentiment Analysis...')
                        # write_current_status(status_area, 'Finished Processing!! ')
                        # tot = len(df1.index)
                        # i=0
                        if model_predict != 'savani' and model_predict != 'All': #dilbert
                            for text in df1.iloc[:, 0]:
                                rsult = voiceAnalysisServices.perform_sentiment_analysis(text,return_all=False, model=model_predict)
                                sentiments.append(rsult[0])
                                polarity.append((rsult[1]))
                            df1["sentiment"] = sentiments
                            df1["polarity"] = polarity
                            progress_bar.progress(80, 'Plotting...!!')
                            plot_to_charts(df1)
                            progress_bar.progress(100, 'Done, Finished Processing!!')
                        elif (model_predict == 'savani' or model_predict=='roberta') and model_predict != 'All':
                            df = voiceAnalysisServices.perform_sentiment_analysis(df1,return_all=True, model=model_predict, isFileUpload=True)
                            progress_bar.progress(80, 'Plotting...!!')
                            plot_to_charts_savani(df)
                            progress_bar.progress(100, 'Done, Finished Processing!!')
                        elif model_predict =='All-SS':
                            print(model_predict)
                            df = voiceAnalysisServices.perform_sentiment_analysis(df1,return_all=True, model='savani', isFileUpload=True)
                            progress_bar.progress(50, 'Plotting...!!')
                            plot_to_charts_savani(df)
                            df = voiceAnalysisServices.perform_sentiment_analysis(df1,return_all=True, model='samLowe', isFileUpload=True)
                            progress_bar.progress(50, 'Plotting...!!')
                            plot_to_charts_savani(df)
                            progress_bar.progress(100, 'Done, Finished Processing!!')
                except Exception as ex:
                    st.error("Error occurred during sentiment/textual analysis.")
                    st.error(str(ex))
                    traceback.print_exc()
                finally:
                    # uploadButtonState["value"] = True
                    st.session_state.uploadButtonState = uploadButtonState
        else:
            st.sidebar.write('Compare not available for uploaded file(s) at present. Please select a different model')
        # Perform audio tr


@pandas_cache
def read_the_csv_txt_file(text_csv_file):
    df = pd.read_csv(text_csv_file, delimiter='\r\n')
    return df


def plot_to_charts(df1):
    with st.spinner('Processing...'):
        col1, col2 = st.columns([1, 1])
        # Let's count the number of texts by sentiments
        sentiment_counts = df1.groupby(["sentiment"]).size()
        # print(sentiment_counts)
        # Let's visualize the sentiments
        fig = plt.figure(figsize=(1, 1), dpi=600)
        ax = plt.subplot(111)
        sentiment_counts.plot.pie(ax=ax, autopct="%1.2f%%", startangle=270, fontsize=4, label="")
        col1.pyplot(fig)
        # ---------
        # Let's count the number of texts by sentiments
        cutoff = np.linspace(-1.0, 1.0, num=6).round(decimals=1)
        # labels = ['r1', 'r2', 'r3', 'r4', 'r5']
        print(df1)
        # df1['group'] = pd.cut(df1['polarity'], bins=cutoff, labels=labels)
        # Let's visualize the sentiments
        fig = plt.figure(figsize=(4, 3), dpi=600)
        counts, bins = np.histogram(df1.polarity)
        print(f'counts:{counts}')
        print(f'bins:{bins}')
        data = df1.polarity
        density,bins, _ = plt.hist(x=data, bins=bins, range=cutoff, color='grey', linewidth=0.1, edgecolor="white")
        for x, y, num in zip(bins, density, counts):
            if num != 0:
                plt.text(x+0.03, y, num, fontsize=5, rotation=0)  # x,y,str
        plt.xlabel('Polarity')
        plt.xticks(bins, color='black', fontsize=4)
        plt.yticks([0, 50, 200, 500, 1000, 2000], color='blue', fontsize=4)
        col2.pyplot(fig)
        st.markdown("<font size='5'>  Model: {} </font>".format(model_select), unsafe_allow_html=True)


def plot_to_charts_savani(df1):
    with st.spinner('Processing...'):
        col1, col2 = st.columns([1, 1])
        # Let's count the number of texts by sentiments
        sentiment_counts = df1.groupby(["sentiment"]).size()
        print(f'sentiment_counts:{sentiment_counts}')
        # Let's visualize the sentiments
        fig = plt.figure(figsize=(1, 1), dpi=600)
        ax = plt.subplot(111)
        sentiment_counts.plot.pie(ax=ax, autopct="%1.2f%%", startangle=270, fontsize=4, label="")
        col1.pyplot(fig)
        # ---------
        #emotions percentage
        sentiment_pct = df1['sentiment'].value_counts(normalize=True) * 100
        print(f'sentiment_pct{sentiment_pct}')
        print(f'sentiment_counts_count{sentiment_counts.count()}')
        fig = plt.figure(figsize=(4, 3), dpi=600)
        df2 = pd.DataFrame(sentiment_pct)
        df2.rename(columns={'proportion': 'percentage'}, inplace=True)
        df2['emotions'] = df2.index
        # fig = df2.plot.hist(alpha=0.5)

        plt.bar(df2['emotions'].to_list(), df2['percentage'].to_list(), alpha=0.5)

        plt.xlabel('Sentiments')
        plt.ylabel('Percentage')
        plt.title('Sentiments Percentage')
        col2.pyplot(fig)
        st.markdown("<font size='5'>  Model: {} </font>".format(model_select), unsafe_allow_html=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        st.error("Error occurred during sentiment/textual analysis.")
        st.error(str(ex))
        traceback.print_exc()
    finally:
        uploadButtonState["value"] = True
        st.session_state.uploadButtonState = uploadButtonState

