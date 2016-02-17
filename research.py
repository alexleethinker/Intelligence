#!/usr/bin/env python
#this program takes a quoted string as its one argument
#parallize urls and cut time down
import httplib
from multiprocessing.pool import ThreadPool

print("\nEnter your subject of research")
search_string = str(raw_input())

def nice_print(line):
	#prints the 
        len_line = len(line)
        i = 0
        LINE_LENGTH = 80#default terminal size
        for j in range(1,len_line/LINE_LENGTH+1):
                i += LINE_LENGTH
                if (i > len_line):      break
                if (not (' ' == line[i])):
                        while (line[i] != ' '):
                                i -= 1
                        if (i != -1):
                                line = line[:i] + '\n' + line[i+1:]
                        i += 1#next line char move up
		else:#if there is a space at line
			if (i != -1):
				line = line[:i] + '\n' + line[i+1:]
			i += 1
        return line

def hex_to_str(s):
	#take a two digit hex string to a ascii character
	if (len(s) != 3):	return s
	s1 = s[1:2]
	s2 = s[2:3]
	if (s1 in '0123456789'):
		s1 = int(s1)
	else:
		s1 = s1.lower()
		s1 = ord(s1) - 87
	if (s2 in '0123456789'):
		s2 = int(s1)
	else:
		s2 = s2.lower()
		s2 = ord(s2) - 87
	return chr(s1*16 + s2)

def decode_url(t):
        #fix any percent encoded url
        if (not ('%' in t or '&amp;' in t)):    return t
        while 1:
                if (t.find('%') == -1): break
                pos = t.find('%')
                t = t[0:pos] + hex_to_str(t[pos:pos+3]) + t[pos+3:]
        #fix ampersand encoding
        while 1:
                if (t.find('&amp;') == -1):     break
                pos = t.find('&amp;')
                t = t[0:pos+1] + t[pos+5:]
        return t

def decode_page(t):
        if (not ('&#' in t or '  ' in t)):   return t
        #fix ampersand encoding
        while 1:
                if (t.find('&#') == -1):        break
                pos = t.find('&#') + 2
                end = t.find(';',pos)
                if (end - pos <= 3):
                        try:    number = int(t[pos:end])#number to encode
                        except: number = 32
                        if (number < 250):
                                t = t[0:pos-2] + chr(number) + t[end+1:]
                        else:   t = t[0:pos-2] + t[pos:]#remove &# if not using$
                else:   t = t[0:pos-2] + t[pos:]
	while 1:
		if (t.find('  ') == -1):	break
		t = t[:t.find('  ')] + t[t.find('  ')+1:]
        return t

def find_url(searchy_string):
	#get like 10ish google search results
	s= "+".join(searchy_string.split(' '))
	url = "/search?q=" + str(s)
	#HTTPS stuff
	c = httplib.HTTPSConnection("www.google.com")
	c.request("GET",url)
	response = c.getresponse()
	#print response.status, response.reason
	data = response.read()
	#print "title: " + data[data.find('<title')+7:data.find("</title>")]
	#search for googles first result
	near_match = 'class="r"'
	pos = data.find('id="search"')
	count = 0
	results = []
	while 1:#handles if there is not url there a first time
		pos = data.find(near_match,pos+1)
		match = '<a href="'
		len_match = len(match)
		index2 = data.find(match,pos) + len_match
		endex2 = data.find('"',index2)
		final_url = ''
		if not (index2 == -1 or endex2 == -1):
			#print str(index2) + " to " + str(endex2)
			#print "near match " + str(near_match) + " pos " + str(pos)
			first_result = data[index2:endex2]
			if (not ('>' in first_result or '<' in first_result)):
				final_url = first_result[first_result.find('url?q=')+6:first_result.find('&amp;')]
		if ('http' in final_url):
			results.append(decode_url(final_url))
		else:
			count += 1#add to loop counter
		if (count > 20):#max limit search at 20
			print("could not find a url")
			break
		elif (len(results) >= 10):
			#print("found some urls")
			break#found enough results
	#search for duplicates and remove them
	for url in results:
		while results.count(url) != 1:
			results.reverse()#flips list so last duplicate is removed first
			results.remove(url)#removes all duplicates
			results.reverse()#flips list back
	return results

def get_base_domain(u):
	#hacky hack to get a base domain for all websites
	if ('/' in u and '//' in u):
		return u[u.find('//')+2:u.find('/',u.find('//')+2)]
	else:	return u

def get_back_url(u):
	#hacky hack to get url after base domain
	return u[u.find(get_base_domain(u))+len(get_base_domain(u)):]

def remove_html(html):
	while ('<script' in html and '</script>' in html):
		#stuff in these tags I dont want
		next = html.find('<script')
		end = html.find('</script>')
		if (next < end):
			html = html[:next] + html[end+len('</script>'):]
	while ('<' in html or '>' in html):
		if (html.find('<') < html.find('>')):
			if (html.find('<') == -1):
				break
			else:
				html = html[:html.find('<')] + html[html.find('>')+1:]
		else:
			if (html.find('>')+1 == 0):
				break
			else:
				html = html[html.find('>')+1:]
	while ('\n' in html or '\t' in html):
		#replace white space stuff with a space
		if ('\n' in html):
			html = html[:html.find('\n')] + " " + html[html.find('\n')+1:]
		else:
			html = html[:html.find('\t')] + " " + html[html.find('\t')+1:]
	while ('\r' in html):
		#replace white space stuff with a space
		if ('\r' in html):
			html = html[:html.find('\r')] + " " + html[html.find('\r')+1:]
	return html

def get_page_quotes(url_to_follow):
	if ('http://' in url_to_follow):#http
		c = httplib.HTTPConnection(get_base_domain(url_to_follow))
		c.request("GET",get_back_url(url_to_follow))
		response = c.getresponse()
		data = response.read()
	elif ('https://' in url_to_follow):#https
		c = httplib.HTTPSConnection(get_base_domain(url_to_follow))
		c.request("GET",get_back_url(url_to_follow))
		response = c.getresponse()
		data = response.read()
	else:
		data = ''
	important_words = []
	word_length = [len(j) for j in search_string.split(' ')]
	#rank by length
	temp = search_string.split(' ')
	while temp != []:
		temp.reverse()
		word_length.reverse()
		l = temp[word_length.index(max(word_length))]
		important_words.append(l)
		while l in temp:
			i = temp.index(l)
			temp.pop(i)
			word_length.pop(i)
		temp.reverse()
		word_length.reverse()
	if (data == ''):
		return ''
	else:
		quotes = []
		pos = data.find('<body')#data is in the body of the html
		for i in xrange(0,20):#try a couple of paragraph tags to see if there is any useful data
			pos = data.find('<p',pos+1)#useful data is in the paragraph tags
			if (pos == -1):
				break#lol
			endex = data.find('</p>',pos+1)
			if (endex == -1):
				break#lol
			#kinda need to watch out with filtering everything through the remove html function. lots of loops there
			temp_quote = data[pos:endex]
			pos = endex#make sure to leave that paragraph, after im done
			#if two most important words are in this quote
			if (len(important_words) > 1):
				if (temp_quote.lower().find(important_words[0].lower()) != -1 or temp_quote.lower().find(important_words[1].lower()) != -1):#precheck
					temp_quote = decode_page(remove_html(temp_quote))
					if (temp_quote.lower().find(important_words[0].lower()) != -1 or temp_quote.lower().find(important_words[1].lower()) != -1):
						quotes.append(temp_quote + "\nsource: " + str(url_to_follow))
			else:
				if (temp_quote.lower().find(important_words[0].lower()) != -1):#precheck, so i dont waste a bunch of loops
					temp_quote = decode_page(remove_html(temp_quote))
					if (temp_quote.lower().find(important_words[0].lower()) != -1):
						quotes.append(temp_quote + "\nsource: " + str(url_to_follow))
		return quotes

def get_related_terms(list_of_quotes,search_string):
	#output a search string that is related to the search_string entered
	#but uses new words from the quotes, part of the discovery engine
	word_count = {}
	for quotes in list_of_quotes:
		for phrase in quotes:
			phr = ' ' + phrase.lower() + ' '
			words = phrase.split(' ')
			for word in words:
				if (words.count(word) > 1):
					for p in xrange(0,words.count(word)):
						words.remove(word)
				try:
					value = word_count[word.lower()]
				except:
					value = 0
				#weight by word length and frequency
				word_count[word.lower()] = (value + phr.count(' ' + word.lower() + ' '))*(len(word))
	#remove search_terms and common words
	for garbage in search_string.split(' ') + ['and','the','they','is','not','be','to','of','that','have','with','his','her','a','in','i','it','for','he','as','do','at','but','this','was']:
		try:
			word_count.pop(garbage)
		except:
			pass
	for word in word_count.keys():#could be a large search can be pruned for optimization
		for searchy_thing in search_string.split():
			if (searchy_thing in word and len(searchy_thing) > 3):
				try:
					word_count.pop(word)
				except:#make sure doesnt fail if it cant find it
					pass
		if ('http' in word or '.com' in word or '.org' in word):#no urls in related word
			try:
				word_count.pop(word)
			except:
				pass
	#print("list with stuff removed: " + str(word_count))
	if (len(word_count) > 0):
		return str(word_count.keys()[word_count.values().index(max(word_count.values()))])
	else:
		return ""

def get_context(list_of_quotes,a_term,search_string):
	if (a_term == ''):
		return ''
	sentences = []
	#get 4 words included with a term in a list of quotes
	len_word = [len(j) for j in search_string.split(' ')]
	if (len(len_word) > 0):
		important_word = search_string.split(' ')[len_word.index(max(len_word))]
	else:#if there is no important word
		important_word = 'important'
	for quotes in list_of_quotes:
		for phrase in quotes:
			pos = 0
			while pos > -1:
				pos = phrase.lower().find(a_term.lower(),pos+1)
				if (pos - 55 < 0):#prevents like weird string stuff, like negative wrapping
					v = 0
				else:
					v = pos - 55
				if (important_word.lower() in phrase.lower()[v:pos+55]):#check if search term is close by
					space_end = phrase.find(' ',pos+1)
					important_start = phrase.lower().find(important_word.lower(),v)
					if (pos < important_start):#if a search term is in the middle then get the sentence between the start term and space
						for i in range(0,6):#sets the end space after the search term not the related word
							space_end = phrase.find(' ',important_start+1)
						important_start = pos
					else:#if related word is after search term, set a couple spaces after it
						for i in range(0,6):
							space_end = phrase.find(' ',space_end+1)
					if not (space_end == -1 or important_start == -1):
						sentences.append(phrase[important_start:space_end])
				else:
					space_end = pos
					for i in range(0,7):
						space_end = phrase.find(' ',space_end+1)
					if not (space_end == -1 or pos == -1):
						sentences.append(phrase[pos:space_end])
	#score sentences, find an average one
	long_words = []
	freq = {}
	for sentence in sentences:
		for word in sentence.split(' '):
			if (len(word) > 3 and not(word in long_words)):
				long_words.append(word)
	for word in long_words:
		for quotes in list_of_quotes:
			for phrase in quotes:
				try:
					value = freq[word.lower()]
				except:
					value = 0
				freq[word.lower()] = value + phrase.lower().count(word.lower())
	for word in freq.keys():
		freq[word] = freq[word]*len(word)
	try:
		most_long_word = freq.keys()[freq.values().index(max(freq.values()))].lower()
	except:
		most_long_word = a_term.lower()
	good_sentences = []
	for sentence in sentences:
		if (most_long_word.lower() in sentence.lower()):
			good_sentences.append(sentence)
	total_related = ' '.join(good_sentences)
	best_sentence = sentences[0]
	best = 0
	for senx in good_sentences:
		score = 0
		for word in senx.split(' '):
			score += int(total_related.lower().find(word.lower())*3.5) + len(word)
		if (best < score):
			best_sentence = senx
			best = score
	return best_sentence

def ranked_quotes(list_of_quotes,search_string,urls):
        #rank the list_of_quotes
        rating = []
        total_quote = ''
        s_terms = search_string.split(' ')
        for source in list_of_quotes:
		total_quote += ' '.join(source)
        #make a list of important words to score for
        old_words = total_quote.split(' ')
        words = []
        for word in old_words:
                if not (word in words):
                        if not ('http' in word):
                                words.append(word)
        for garbage in ['and','the','they','is','not','be','to','of','that','have','with','his','her','a','in','it','for','he','as','do','but','this','was']:
                if (garbage in words):
                        words.remove(garbage)
        word_count = []
        for word in words:
                word_count.append(total_quote.count(word))
        #
        # scoring
        #   and
        # output!
	#
	best_score = 0
	for source in list_of_quotes:
                for quote in source:
                        score = 0
                        for word in words:
                                if (word in quote):
                                        if (word in s_terms):
                                                score += word_count[words.index(word)]*(11*len(word))
                                        elif ('sell' in word or 'buy' in word or 'blog' in word or 'share' in word):
						#aggressively decrease score of advertisements and blogs
                                                score -= word_count[words.index(word)]*(20*len(word))
					elif ('http' in word or 'source' in word):
						pass#dont let urls effect the score
					elif ('i' == word.lower() or 'my' == word.lower()):
						#aggressive score against use of self centered words, means it might be a commenter
                                                score -= word_count[words.index(word)]*(100)
                                        else:
                                                score += word_count[words.index(word)]*(len(word))
			score = score/(len(quote)**(3/15))
			if (score > best_score):
				best_score = score
				final_q = quote
	try:
		a = final_q
	except:
		final_q = ''
	return final_q

def discover(list_of_quotes,search_string,related_word):
	#use related terms and quotes to find a cool quote from a website kinda about your search string
	s = search_string.split(' ')
	len_word = [len(j) for j in s]
	important_term1 = s[len_word.index(max(len_word))]
	while important_term1 in s:
		s.remove(important_term1)
	if (len(s) > 0):
		len_word = [len(j) for j in s]
		important_term2 = s[len_word.index(max(len_word))]
		new_search = related_word + " " + important_term1 + " " + important_term2
	else:
		new_search = related_word + ' and ' + important_term1
	#get a quote from a new article
	len_word = [len(i) for i in new_search.split(' ')]
	important = new_search.split(' ')[len_word.index(max(len_word))]
	new_list_of_quotes = []
	urls = find_url(new_search)
	results = ThreadPool(20).imap_unordered(get_page_quotes,urls[0:5])
	for source in results:
		new_list_of_quotes.append(source)
	best_partial_quote = get_context(new_list_of_quotes,important,new_search)
	count = 0
	for source in new_list_of_quotes:
		for quote in source:
			if (best_partial_quote in quote):
				return quote
		count += 1
	#if no new, the old quote will suffice
	old_context = get_context(list_of_quotes,related_word,search_string)
	for source in list_of_quotes:
		for quote in source:
			if (old_context in quote):
				return quote
	return "no discovered quote found"

#if len(sys.argv) != 2:
#	print("failure due to lack of correct command line argument")
#	exit(1)
#search_term = sys.argv[1]
#next line, finds a list of urls related to research question
search_term = search_string
some_urls = find_url(search_term)
result_quotes = []
#print(some_urls)
#parallel version of getting quotes from a url
results = ThreadPool(20).imap_unordered(get_page_quotes,some_urls[0:4])
for source in results:
	result_quotes.append(source)
if ('new ' in search_term or 'discover' in search_term):
	if ('discover' in search_term):
		search_term = search_term[:search_term.find('discover')] + search_term[search_term.find('discover')+len('discover'):]
	related = get_related_terms(result_quotes,search_term)
	print("related: " + str(related))
	print("context: " + get_context(result_quotes,get_related_terms(result_quotes,search_term),search_term))
	quo = discover(result_quotes,search_term,related)
	print('\n' + nice_print("discover: " + quo) + '\n')
	if ('no discovered quote' in quo):
		print "trying a bunch of new urls\n\n"
		results = ThreadPool(20).imap_unordered(get_page_quotes,some_urls[0:4])
		result_quotes = []
		for source in results:
			result_quotes.append(source)
		related = get_related_terms(result_quotes,search_term)
		print("related: " + str(related))
		print("context: " + get_context(result_quotes,get_related_terms(result_quotes,search_term),search_term))
		print('\n' + nice_print("discover: " + str(discover(result_quotes,search_term))) + '\n')
else:
	best_quotes = ranked_quotes(result_quotes,search_term,some_urls)
	if (len(best_quotes) > 2):
		print('\n' + nice_print("best info: " + best_quotes) + '\n')#print ranked one quote
	else:
		results = ThreadPool(20).imap_unordered(get_page_quotes,some_urls[4:])
		for source in results:
			result_quotes.append(source)
		best_quotes = ranked_quotes(result_quotes,search_term,some_urls)
		print('\n' + nice_print("best info: " + best_quotes) + '\n')#print ranked one quote
#wait before moving on if your in terminal
print("\n\nPress enter to move on")
raw_input()
