import json
import requests
import os
import spacy
import re

def ujwal_annotations(text):
	#Code to add temporal, entityRecognition
	predicted = []
	#nlp1 = 'sebi_ib'
	#doc1 =  nlp1(text)
	#for ent1 in doc1.ents:
	#	predicted.append({"label":ent1.label_, "start":ent1.start_char, "end":ent1.end_char, "text":ent1.text})

	url = "http://0.0.0.0:8000/parse"
	print(text)

	payload = dict(data='locale=en_GB', text=text)
	res = requests.post(url, data=payload)
	#print(res)
	data = res.json()
	#print(data)
	for ele in data:
		predicted.append({"label":ele['dim'], "start":ele['start'], "end":ele['end'], "text":ele['body']})
	annotated_text = predicted
	return annotated_text

def sathvik_annotations(text):
	e,c,a,pe = identifying_parts(text)
	rule = text		
	ans = []		
	for ent in e:
		match_obj = re.search(re.escape(ent),rule)
		if match_obj:
			span_obj =  match_obj.span()
			ans.append({"start":span_obj[0],"end":span_obj[1],"label":"ENT","text":rule[span_obj[0]:span_obj[1]]})
		for ent in c:
			match_obj = re.search(re.escape(ent),rule)
			if match_obj:
				span_obj =  match_obj.span()
				ans.append({"start":span_obj[0],"end":span_obj[1],"label":"COND","text":rule[span_obj[0]:span_obj[1]]})
		for ent in a:
			match_obj = re.search(re.escape(ent),rule)
			if match_obj:
				span_obj =  match_obj.span()
			ans.append({"start":span_obj[0],"end":span_obj[1],"label":"ACT","text":rule[span_obj[0]:span_obj[1]]})
	return ans


bullet_regex = re.compile("^(\(?)([0-9]+|[a-z]+)((\)\.)|(\.)|\))")
first_index_regex = re.compile("^[0-9]+[A-Z]?.\ *?\(1\)")

def identifying_parts(rule):
	# doc = nlp2(rule)
	entities = []
	for ent in shravya_annotations(rule):
		entities.append((ent["start"], ent['end'],ent['label'],ent['text']))
	# print(entities)
	#entities = shravya_annotations(rule)
	mini_entities = []
	for jele in entities:
			s,e,i,x = jele
			mini_entities.append({"start":s,"end":e,"label":i})
	
	e = []
	condition = []
	action = []
	e_cleaned = []
	
	entities = {
				"cleanedUpEnts": [rule[ele['start']:ele['end']] for ele in mini_entities if ele['label'] not in ['Transaction','Value','Objective','Legal Term','Legal Doc']]
			}
	
	Conditiontype1 = ['if', 'where', 'while', 'after', 'on', 'upon', 'in the case', 'in case']
	Conditiontype2 = ['whose', 'who', 'while', 'if', 'having', 'unless', 'that', 'required','once']
	
	rule = re.sub(first_index_regex,'',rule.strip())
	rule = re.sub(bullet_regex,"",rule)
	
	toked_rule = rule.lower().split(' ')
	start_token = toked_rule[0]
		
	all_ents = entities['cleanedUpEnts']
	parsed_ents = all_ents
	
	all_spans = []

	for ent in all_ents:
		try:
			match_obj = re.search(re.escape(ent),rule)
			span_obj = match_obj.span()
			all_spans.append(span_obj)
		except:
			pass
	
	none_flag = True
	if start_token in Conditiontype1 or  \
		toked_rule[0:3] == ['in','the','case'] or toked_rule[0:2] == ['in','case']:
		#Get closest entity:
		
		min_ele_index = all_spans.index(min(all_spans, key=lambda span_: span_[0]))

		e.append(all_ents[min_ele_index])
		e_cleaned.append(parsed_ents[min_ele_index])
		
		comma_index = rule.find(',')
		condition.append(rule[0:comma_index])

		shall_index = rule.find('shall')
		may_index = rule.find('may')
		
		shall_index = len(rule) if shall_index == -1 else shall_index
		may_index = len(rule) if may_index == -1 else may_index
		
		min_index  = min(shall_index,may_index)
		action.append(rule[min_index:])
		none_flag = False
	
	shall_index = rule.find('shall')
	may_index = rule.find('may')
	shall_index = len(rule) if shall_index == -1 else shall_index
	may_index = len(rule) if may_index == -1 else may_index
	min_index  = min(shall_index,may_index)
	
	if any([ele for ele in Conditiontype2 if ele in rule[:min_index]]):
		# Any before occurence shall
		all_condition_indices = [rule[:min_index].find(ele) for ele in Conditiontype2]
		if any([ele != -1 for ele in all_condition_indices]) and len(all_spans) > 0:            
			min_ele_index = all_spans.index(min(all_spans,key=lambda span_:span_[0]))
			
			condition_words_pos = [rule.find(ele) for ele in Conditiontype2]
			condition_words_pos = [len(rule) if ele == -1 else ele for ele in condition_words_pos]
			min_condition_word_pos = min(condition_words_pos)
			min_condition_word = Conditiontype2[condition_words_pos.index(min_condition_word_pos)] 
			all_possible_entities = [ele for ele in all_spans if ele[0] < min_condition_word_pos]

			if len(all_possible_entities) > 0:
				min_entity_index = all_spans.index(min(all_possible_entities,key = lambda span_:span_[0]))
				e.append(all_ents[min_ele_index])
				e_cleaned.append(parsed_ents[min_ele_index])
				shall_index = rule.find('shall')
				may_index = rule.find('may')

				shall_index = len(rule) if shall_index == -1 else shall_index
				may_index = len(rule) if may_index == -1 else may_index
				min_index  = min(shall_index,may_index)

				condition.append(rule[:min_index])
				action.append(rule[min_index:])
				none_flag = False
	
	comma_part = rule[min_index:]
	comma_flag = False
	if comma_part[:5] == "shall":
		if ',' in comma_part[5:8]:
			comma_flag = True
	elif comma_part[:3] == "may":
		if ',' in comma_part[3:5]:
			comma_flag = True
	if comma_flag:
		# immediately after a shall ","
		# 
		sub_rule = rule[min_index:]
		commas = [m.start() for m in re.finditer(',', rule[min_index:])]
		indices_list = [ele for ele in all_spans if ele[0] < min_index]
		if len(commas) >= 2 and len(indices_list) > 0:
			min_entity_index = all_spans.index(min(indices_list,key = lambda span_:span_[0]))
			
			e.append(all_ents[min_entity_index])
			e_cleaned.append(parsed_ents[min_entity_index])
			
			condition.append(sub_rule[commas[0]:commas[1]])
			action.append(sub_rule[commas[1]:])
			none_flag = False
			
	if none_flag:
		# Main 
		indices_list = [ele for ele in all_spans if ele[0] < min_index]
		if len(indices_list) > 0:
			min_entity_index = all_spans.index(min(indices_list,key = lambda span_:span_[0]))
			e.append(all_ents[min_entity_index])
			e_cleaned.append(parsed_ents[min_entity_index])
			
			condition.append("nil")
			shall_index = rule.find('shall')
			may_index = rule.find('may')

			shall_index = len(rule) if shall_index == -1 else shall_index
			may_index = len(rule) if may_index == -1 else may_index

			min_index  = min(shall_index,may_index)
			action.append(rule[min_index:])
	
	return e, condition, action, e_cleaned

def shravya_annotations(text):
	#Code to add ner, ..
	predicted = []
	nlp1 = spacy.load("/home2/shravya.k/objective_final/model-best") #load the best model
	nlp2 = spacy.load("/home2/shravya.k/authority_final/model-best") #load the best model
	nlp3 = spacy.load("/home2/shravya.k/subject-individual_final/model-best") #load the best model
	nlp4 = spacy.load("/home2/shravya.k/subject-organisation_final/model-best") #load the best model
	nlp5 = spacy.load("/home2/shravya.k/date_final/model-best") #load the best model
	nlp6 = spacy.load("/home2/shravya.k/legal_doc_final/model-best") #load the best model
	nlp7 = spacy.load("/home2/shravya.k/legal_term_final/model-best") #load the best model
	nlp8 = spacy.load("/home2/shravya.k/object_general_final/model-best") #load the best model
	nlp9 = spacy.load("/home2/shravya.k/transaction_final/model-best") #load the best model
	nlp10 = spacy.load("/home2/shravya.k/value_final/model-best") #load the best model


	doc1 = nlp1(text)
	for ent1 in doc1.ents:
		predicted.append({"label":ent1.label_, "start":ent1.start_char, "end":ent1.end_char, "text":ent1.text})

	doc2 = nlp2(text)
	for ent2 in doc2.ents:
		predicted.append({"label":ent2.label_, "start":ent2.start_char, "end":ent2.end_char, "text":ent2.text})

	doc3 = nlp3(text)
	for ent3 in doc3.ents:
		predicted.append({"label":ent3.label_, "start":ent3.start_char, "end":ent3.end_char,  "text":ent3.text})

	doc4 = nlp4(text)
	for ent4 in doc4.ents:
		predicted.append({"label":ent4.label_, "start":ent4.start_char, "end":ent4.end_char,  "text":ent4.text})

	doc5 = nlp5(text)
	for ent5 in doc5.ents:
		predicted.append({"label":ent5.label_, "start":ent5.start_char, "end":ent5.end_char,  "text":ent5.text})

	doc6 = nlp6(text)
	for ent6 in doc6.ents:
		predicted.append({"label":ent6.label_, "start":ent6.start_char, "end":ent6.end_char,  "text":ent6.text})

	doc7 = nlp7(text)
	for ent7 in doc7.ents:
		predicted.append({"label":ent7.label_, "start":ent7.start_char, "end":ent7.end_char,  "text":ent7.text})

	doc8 = nlp8(text)
	for ent8 in doc8.ents:
		predicted.append({"label":ent8.label_, "start":ent8.start_char, "end":ent8.end_char,  "text":ent8.text})

	doc9 = nlp9(text)
	for ent9 in doc9.ents:
		predicted.append({"label":ent9.label_, "start":ent9.start_char, "end":ent9.end_char,  "text":ent9.text})

	doc10 = nlp10(text)
	for ent10 in doc10.ents:
		predicted.append({"label":ent10.label_, "start":ent10.start_char, "end":ent10.end_char,  "text":ent10.text})

	annotated_text = predicted
	#predicted = annotated_text
	return annotated_text

file1 = open("case_files.txt","r")
#all_samples = file1.readlines()
full_list = []
grand_json_all_annotations = {}
text = file1.read()
#text = input("Enter your value: ")#for text in all_samples:
if 1:
	if text:
		grand_json_all_annotations = {}
		anotations_list = []
		anotations_list.extend(shravya_annotations(text))
		#anotations_list.extend(sathvik_annotations(text))
		print(text)
		#print(anotations_list)
		#anotations_list.extend(ujwal_annotations(text))
		if len(anotations_list):
			grand_json_all_annotations["sub-regulation"] = text
			grand_json_all_annotations['number'] = len(anotations_list)
			grand_json_all_annotations['annotations'] = anotations_list
			print(grand_json_all_annotations)
			full_list.append(grand_json_all_annotations)
		#print(full_list)
print(full_list)
with open("grand_annotations.json", "w") as outfile: 
	json.dump(full_list, outfile)
