# Import packages
import logging
import os
import string

import pandas as pd
import spacy
from spacy.lang.en.stop_words import STOP_WORDS as stopwords

from code.filter_files import load_in_tree

logging.basicConfig(level=logging.DEBUG)

# Load spacy model.
nlp = spacy.load('en_core_web_sm')


def get_basic_stats(tree, word_list):
    dictionary_list = list()

    for elem in tree.findall(".//*[@type='occupation']"):
        dictionary = dict()
        if any('id' in key for key in elem.attrib.keys()) and 'def' in elem.attrib['id']:
            occupation = nlp(elem.text)
            occupation = [token.lemma_.lower() for token in occupation if token.text not in stopwords]
            if any(token in occupation for token in word_list):
                occupation = ' '.join(token for token in occupation if token not in string.punctuation)
                dictionary['occupation'] = occupation
                dictionary['year'] = elem.attrib['id'][1:5]
                dictionary['role'] = 'defendant'
                dictionary['occupationId'] = elem.attrib['id']
                dictionary_list.append(dictionary)

        elif any('inst' in key for key in elem.attrib.keys()) and 'def' in elem.attrib['inst']:
            occupation = nlp(elem.attrib['value'])
            occupation = [token.lemma_.lower() for token in occupation if token.text not in stopwords]
            if any(token in occupation for token in word_list):
                occupation = ' '.join(token for token in occupation if token not in string.punctuation)
                dictionary['occupation'] = occupation
                label, number, year = elem.attrib['inst'].split('-')
                dictionary['year'] = year[:4]
                dictionary['role'] = 'defendant'
                dictionary['occupationId'] = elem.attrib['inst']
                dictionary_list.append(dictionary)
    return pd.DataFrame(dictionary_list)


def get_person_info(tree, df):
    for i, row in df.iterrows():
        for elem in tree.findall('.//*[@targets]'):
            targets = elem.attrib['targets'].split(' ')
            if any(row.occupationId in target for target in targets):
                df.at[i, 'Id'] = targets[0]

    for i, row in df.iterrows():
        for elem in tree.findall(f".//*[@inst='{row.Id}'][@type='gender']"):
            df.at[i, elem.attrib['type']] = elem.attrib['value']

    return df


def get_more_lookup_ids(tree, df):
    df['punishId'] = 'noPunishment'

    for i, row in df.iterrows():
        for elem in tree.findall(".//*[@targets][@result='criminalCharge']"):
            targets = elem.attrib['targets'].split(' ')
            if any(str(row.Id) in target for target in targets):
                df.at[i, 'offenceId'] = targets[1]
                df.at[i, 'verdictId'] = targets[2]
        for elem in tree.findall(".//*[@targets][@result='defendantPunishment']"):
            targets = elem.attrib['targets'].split(' ')
            if any(str(row.Id) in target for target in targets):
                df.at[i, 'punishId'] = targets[1]

    return df


def find_more_info(tree, df):
    for i, row in df.iterrows():
        for elem in tree.findall(f".//*[@inst='{row.offenceId}']"):
            df.at[i, elem.attrib['type']] = elem.attrib['value']

        for elem in tree.findall(f".//*[@inst='{row.verdictId}']"):
            df.at[i, elem.attrib['type']] = elem.attrib['value']

        for elem in tree.findall(f".//*[@inst='{row.punishId}']"):
            df.at[i, elem.attrib['type']] = elem.attrib['value']

    return df


def add_victim_information(tree, df):
    df['victimId'] = 'noVictim'
    df['victimOccupation'] = df['victimId']

    for i, row in df.iterrows():
        for elem in tree.findall(".//*[@targets][@result='offenceVictim']"):
            targets = elem.attrib['targets'].split(' ')
            if any(str(row.offenceId) in target for target in targets):
                df.at[i, 'victimId'] = targets[1]

        for elem in tree.findall(".//*[@targets][@result='persNameOccupation']"):
            targets = elem.attrib['targets'].split(' ')
            if any(str(row.victimId) in target for target in targets):
                for elem in tree.findall(f".//*[@id='{targets[1]}']"):
                    occupation = nlp(elem.text)
                    occupation = [token.lemma_.lower() for token in occupation if token.text not in stopwords]
                    occupation = ' '.join(token for token in occupation if token not in string.punctuation)
                    df.at[i, 'victimOccupation'] = occupation

    return df


def fill_rows(df):
    fill_dictionary = {'punishmentCategory': 'noPunishment',
                       'punishmentSubcategory': 'noPunishment',
                       'verdictSubcategory': 'unknown',
                       'verdictCategory': 'unknown'}

    for col, fill in fill_dictionary.items():
        df[col].fillna(fill, inplace=True)

    df.dropna(inplace=True)
    assert sum(df.isnull().sum()) == 0
    return df


def clean_df(df):
    df = fill_rows(df)

    for col in list(df.columns):
        if 'Id' in col:
            df.drop(col, axis=1, inplace=True)

    return df


def run():
    defendant_folder = '../data/defendants/'
    word_list = ['servant', 'maid']

    complete_df = pd.DataFrame()

    for file in os.listdir(defendant_folder):
        tree = load_in_tree(defendant_folder + file)
        df = get_basic_stats(tree, word_list)
        df = get_person_info(tree, df)
        df = get_more_lookup_ids(tree, df)
        df = find_more_info(tree, df)
        df = add_victim_information(tree, df)
        complete_df = complete_df.append(df)

    complete_df = clean_df(complete_df)

    complete_df.to_csv('../data/complete_defendants.csv', index=False)


if __name__ == '__main__':
    run()
