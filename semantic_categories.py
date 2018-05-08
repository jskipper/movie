# Author: teh Flomeister
import gensim
from scipy import spatial
import pprint
from time import sleep
import json
import numpy as np
import sys
import os
from text_utils import process_sentence
from text_utils import cut_capsules
import retinasdk

with open('NLTK_stops.txt', 'r') as stop:
    stops = stop.read().splitlines()

def process_input(item, mode):
    # processing text
    if mode == 0:
        if len(item) == 1:
            output = 0
        else:
            output = ' '.join(item[1:])

	return output
    # processing image labels
    elif mode == 1:
	output = 0
        outputs = []
        for it in item:

            if len(it) > 1:
                outputs.extend(it[1:]) 

            else:
                output = 0

	if outputs:
	    return outputs

        else:
	    return output

    # processing faces
    else:
        output = item
	return output

def process_capsules(capsules, stops, delay):

    new_caps = []
    output_js = []

    for i in range(len(capsules)):

        capsules[i]['text'] = process_sentence(capsules[i]['text'].split(' '), stops)
        capsules[i]['text'] = [word for word in capsules[i]['text'] if word not in stops]

        text  = process_input(capsules[i]['text'], 0)
	labels = process_input(capsules[i]['labels'], 1)
	faces = process_input(capsules[i]['faces'], 2)

        new_caps.append([capsules[i]['time'], text, labels, faces])
	output_js.append({'time': capsules[i]['time'], 'text': text, 'labels': labels, 'faces': faces})
	#print text
    sorted(new_caps, key = lambda x: int(x[0]))


    with open('sorted_data_1804_rcnn_full_delay_%d.json' % delay, 'w') as wr:
	json.dump(output_js, wr)

    #for c in new_caps[:175]:
    #    print c

    return new_caps

def make_vectors_cortical(word, labels, w_capsule, l_capsule, vecs):

    liteClient = retinasdk.LiteClient("557d9940-40ab-11e8-9172-3ff24e827f76")
    sims = {'capsule': [w_capsule, l_capsule], 'word': word, 'labels': []}
    new_vecs = []

    # check if there are new objects detected in this capsule compared to previous ones
    for label in labels:
	if label not in vecs:
	    new_vecs.append(label)
 
    if new_vecs:
	vecs.extend(new_vecs)
	for vec in vecs:
	    try:
	        sims['labels'].append([vec, liteClient.compare(str(vec), str(word))])
	        #print 'CAPSULE: ', w_capsule
	    except:
		pass
    else:
	for vec in vecs:
	    try:
	        sims['labels'].append([vec, liteClient.compare(str(vec), str(word))])
	        #print 'CAPSULE: ', w_capsule
	    except:
		pass

    return sims, vecs
        

# SECOND method to get word similarity
# compares each label with a word and records the capsule origin of each label/word
# returns the similarities between each label and a given word
# need to feed in the model, the subtitle word to compare, the labels to compare, the word's original capsule, the labels' original capsule and 
# image labels seen so far for this capsule (already compared)
# VECS collects for each capsule the labels seen in all the capsules surrounding it (towards the left)
def make_vectors_word2vec(model, word, labels, w_capsule, l_capsule, vecs):
    # known words to the vocabulary
    known = model.wv
    sims = {'capsule': [w_capsule, l_capsule], 'word': word, 'labels': []}
    new_vecs = []
    # check if there are new objects detected in this capsule compared to previous ones
    for label in labels:
	if label not in vecs and label in known.vocab:
	    new_vecs.append(label)

    # if there are new objects, get similarity and extend the seen_labels list
    if new_vecs:
	vecs.extend(new_vecs)
        for vec in vecs:
  	    sims['labels'].append([vec, model.similarity(vec, word)])
    else:
        for vec in vecs:
  	    sims['labels'].append([vec, model.similarity(vec, word)])

    return sims, vecs

# first method to get word similarity between labels and the subtitles
def make_vectors(model, words, mode):
    # mode 0 is for labels from images - returns individual vectors for each word
    # mode 1 is for subtitle words - returns an averaged vector over all the word in that capsule
    # known_wd is to check if the word is in the vocabulary of the model
    known_wd = model.wv
    
    if mode == 0:

	vectors = []

        for word in words:
	    if word not in vectors and word in known_wd.vocab:
	        vectors.append(word)

	for i in range(len(vectors)):
	    vectors[i] = {'word':vectors[i], 'vector': model.wv[vectors[i]]}

	return vectors

    else:
        vectors = []
        average_vec = []

        for word in words.split():
	    if word in known_wd.vocab:
                vectors.append(model.wv[word])
    
        average_vec = np.array([vec for vec in vectors])
	average_vec = np.average(average_vec, axis=0)
        return average_vec
    
# returns the similarity between each word in the text and each label in labels
def semantic_representation(model, text, labels, word_capsule, label_capsule, delay):

    known_wd = model.wv
    # the output has the capsule number, all the words and the respective labels
    # in the 'labels' key every word in the 'words' key will be tested agains the labels
    # 'delay' tells us from which capsule in the past the labels were extracted
    output = {'capsule': word_capsule, 'delay': delay, 'words': text.split(),'wv_breakdown': [], 'co_breakdown': [] }
    wv_vecs = []
    co_vecs = []

    for word in text.split():
	if word in known_wd.vocab: 

	    word2vec_results, wv_vecs = make_vectors_word2vec(model, word, labels, word_capsule, label_capsule, wv_vecs)
	    cortical_results, co_vecs = make_vectors_cortical(word, labels, word_capsule, label_capsule, co_vecs)
	
	    output['wv_breakdown'].append(word2vec_results)
	    output['co_breakdown'].append(cortical_results)

    return output

def get_distance(model, x, y):
    #dist = np.inner(x, y)/(np.linalg.norm(x)* np.linalg.norm(y))
    #dist = 1 - spatial.distance.cosine(x, y)
    a = model.similar_by_vector(x)
    b = model.similar_by_vector(y)
    dist = model.similarity(a[0][0], b[0][0])
    #print dist
    return dist

# function to set delay of comparison in the past for each capsule
# needs the model, original set of capsules, the capsule of interest and the DELAY for the past
def set_delay(model, capsules, capsule_number, delay):

    cap_results = []

    for i in range(delay, -1, -1):

	capsule_text = capsules[capsule_number][1]

	# will only get similarities if the relevant capsule has labels
        if capsules[capsule_number - i][2] != 0:
	    capsule_labels = capsules[capsule_number - i][2]
	    word_capsule_number = capsules[capsule_number][0]
	    label_capsule_number = capsules[capsule_number - i][0]

	    similarities = semantic_representation(model, capsule_text, capsule_labels, word_capsule_number, label_capsule_number, i)
	    cap_results.append(similarities)

	else:
	    print 'At %d seconds before, there were no objects for capsule %d' % (i, capsules[capsule_number][0])
    # cap_results will contain the same capsule a few times, depending on the delay
    return cap_results

def main(args):

    data = json.load(open('/home/fgheorghiu/toy_data/semantics/final_capsules_1204_rcnn.json'))
    # an array that has time, text, labels & faces    
    capsules = process_capsules(data, stops, int(args[0]))
    model = gensim.models.KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True, limit=500000)
#    test_data = [[14, 'boy meets girl',['person', 'dog', 'house', 'lawn', 'smile'], 0], 
#		[15, 'architect', ['house', 'glass', 'drawing', 'plan'], 0],
#		[16, 'boss vacation', ['cup', 'book', 'pencil'], 0], 
#		[17, 'joking war', ['paris', 'water', 'bench'], 0]]

    results = []


    # capsules have
    # [0] - capsule time
    # [1] - text or 0
    # [2] - labels or 0
    # [3] - facial emotions or 0
    # Each capsule's words are checked against every label in the past X seconds   
    for i in range(int(args[0]),len(capsules)):
	# only takes capsules with text
	if capsules[i][1] != 0:
            #l1, l2 = semantic_representation(model, capsules[i])

	    # METHOD 2
	    # IMPORTANT - last argument is the desired delay
	    results.append(set_delay(model, capsules, i, int(args[0])))

	    # METHOD 1
	    #results.append([capsules[i][0]])
	    #if l1.size > 1:
   	    #    for word in l2:
	    #        results.append([model.similar_by_vector(l1)[0][0], word['word'], get_distance(model, word['vector'], l1)])

    with open('output_1804_rcnn_full_delay_%d.json' % int(args[0]), 'w') as wr:
        json.dump(results, wr)
#    print model.similarity('architect', 'house')
#    print model.similarity('architect', 'glass')
#    print model.similarity('architect', 'drawing')
#    print model.similarity('architect', 'plan')


if __name__ == '__main__':
    main(sys.argv[1:])

