# Import packages
import logging
import os
import shutil
import xml.etree.ElementTree as ET

import spacy
from spacy.lang.en.stop_words import STOP_WORDS as stopwords

logging.basicConfig(level=logging.DEBUG)

# Load spacy model.
nlp = spacy.load('en_core_web_sm')

defendant_folder = './data/defendants/'
victim_folder = './data/victims/'


def load_in_tree(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()
    return root


def filter_files(file, word_list):
    tree = load_in_tree(file)

    for elem in tree.findall(".//*[@type='occupation']"):
        # Used for the files after 1834.
        try:
            occupation = nlp(elem.attrib['value'])
            occupation = [token.lemma_.lower() for token in occupation if token.text not in stopwords]

            if any(token in occupation for token in word_list):
                if 'def' in elem.attrib['inst']:
                    shutil.copy(file, defendant_folder)
                else:
                    shutil.copy(file, victim_folder)

        # Used for the earlier files
        except:
            if elem.text != None:
                occupation = nlp(elem.text)
                occupation = [token.lemma_.lower() for token in occupation if token.text not in stopwords]

                if any(token in occupation for token in word_list):
                    if 'def' in elem.attrib['id']:
                        shutil.copy(file, defendant_folder)
                    else:
                        shutil.copy(file, victim_folder)


def explore_later_files(file):
    tree = load_in_tree(file)
    for elem in tree.iter('*'):
        print(elem.attrib)


def run():
    original_folder = './exploring_XML/sessionsPapers/'
    original_folder2 = './exploring_XML/ordinarysAccounts/'

    word_list = ['servant', 'maid']

    for file in os.listdir(original_folder2):
        filter_files((original_folder2 + file), word_list)

    #print(
    #    f"Number of files in which a servant is mentioned as a defendant: {len([name for name in os.listdir(defendant_folder)])}.")
    #print(
    #   f"Number of files in which a servant is mentioned as a victim: {len([name for name in os.listdir(victim_folder)])}.")
    #print(f"Number of original files: {len([name for name in os.listdir(original_folder)])}.")

    #print(
        #f"Number of files in which a servant is mentioned as a defendant: {len([name for name in os.listdir(defendant_folder)])}.")
    #print(
        #f"Number of files in which a servant is mentioned as a victim: {len([name for name in os.listdir(victim_folder)])}.")
    print(f"Number of original files: {len([name for name in os.listdir(original_folder2)])}.")


if __name__ == '__main__':
    run()
