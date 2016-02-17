#!/usr/bin/env python
#this program takes a quoted string as its one argument
import sys,httplib
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
	if (not ('%' in t or '&amp;' in t)):	return t
	while 1:
		if (t.find('%') == -1):	break
		pos = t.find('%')
		t = t[0:pos] + hex_to_str(t[pos:pos+3]) + t[pos+3:]
	#fix ampersand encoding
	while 1:
		if (t.find('&amp;') == -1):	break
		pos = t.find('&amp;')
		t = t[0:pos+1] + t[pos+5:]
	return t

def decode_page(t):
	if (not ('&#' in t)):	return t
	#fix ampersand encoding
	while 1:
		if (t.find('&#') == -1):	break
		pos = t.find('&#') + 2
		end = t.find(';',pos)
		if (end - pos <= 3):
			try:	number = int(t[pos:end])#number to encode
			except:	number = 32
			if (number < 250):
				t = t[0:pos-2] + chr(number) + t[end+1:]
			else:	t = t[0:pos-2] + t[pos:]#remove &# if not using ascii
		else:	t = t[0:pos-2] + t[pos:]
	return t

def find_url(searchy_string):
	#get like 10ish google search results
	s= "+".join(searchy_string.split(' '))
	url = "/scholar?q=" + str(s)
	#HTTPS stuff
	c = httplib.HTTPSConnection("scholar.google.com")
	c.request("GET",url)
	response = c.getresponse()
	#print response.status, response.reason
	data = response.read()
	#print "title: " + data[data.find('<title')+7:data.find("</title>")]
	#search for googles first result
	near_match = 'class="gs_rt"'
	pos = 1
	#print "search body: " + str(pos)
	count = 0
	results = []
	while 1:#handles if there is not url there a first time
		pos = data.find(near_match,pos+1)
		match = 'href="'
		len_match = len(match)
		index2 = data.find(match,pos) + len_match
		endex2 = data.find('"',index2)
		final_url = ''
		if (index2 != (-1 + len_match)):
			#print str(index2) + " to " + str(endex2)
			#print "near match " + str(near_match) + " pos " + str(pos)
			first_result = data[index2:endex2]
			if (not ('>' in first_result or '<' in first_result)):
				final_url = first_result
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
	while ('<' in html or '>' in html):
		if (html.find('<') < html.find('>')):
			html = html[:html.find('<')] + html[html.find('>')+1:]
		else:
			html = html[html.find('>')+1:]
	while ('\n' in html):
		#replace white space stuff with a space
		if ('\n' in html):
			html = html[:html.find('\n')] + " " + html[html.find('\n')+1:]
	while ('\t' in html):
		if ('\t' in html):
			html = html[:html.find('\t')] + " " + html[html.find('\t')+1:]
	while ('  ' in html):
		if ('  ' in html):
			html = html[:html.find('  ')] + " " + html[html.find('  ')+2:]
	return html

def get_page_quotes(url_to_follow,search_string):
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
		for i in xrange(0,20):
			pos = data.find('<p',pos+1)#useful data is in the paragraph tags
			if (pos == -1):
				break#lol
			endex = data.find('</p>',pos+1)
			if (endex == -1):
				break#lol
			#add the source reference to every quote
			temp_quote = decode_page(remove_html(data[pos:endex]))
			#if two most important words are in this quote
			if (len(important_words) > 1):
				if (temp_quote.lower().find(important_words[0].lower()) != -1 or temp_quote.lower().find(important_words[1].lower()) != -1):
					quotes.append(temp_quote + "\nsource: " + str(url_to_follow))
			else:
				if (temp_quote.lower().find(important_words[0].lower()) != -1):
					quotes.append(temp_quote + "\nsource: " + str(url_to_follow))
		return quotes

def ranked_quotes(list_of_quotes,urls,search_string):
	#rank the list_of_quotes
	rating = []
	total_quote = ''
	s_terms = search_string.split(' ')
	for source in list_of_quotes:
		for quote in source:
			total_quote += quote + ' '
	#make a list of important words to score for
	old_words = total_quote.split(' ')
	words = []
	for word in old_words:
		if not (word in words):
			if not ('http' in word):
				words.append(word)
	for garbage in ['and','the','they','is','not','be','to','of','that','have','with','his','her','a','in','i','it','for','he','as','do','but','this']:
		if (garbage in words):
			words.remove(garbage)
	word_count = []
	for word in words:
		word_count.append(total_quote.count(word))
	#
	#
	#scoring
	#
	#
	for source in list_of_quotes:
		source_rating = []
		for quote in source:
			score = 0
			for word in words:
				if (word in quote):
					if (word in s_terms):
						score += word_count[words.index(word)]*(6*len(word))
					elif ('sell' in word or 'buy' in word or 'blog' in word):
						score -= word_count[words.index(word)]*(20*len(word))#aggressively decrease score of advertisements and blogs
					else:
						score += word_count[words.index(word)]*(len(word))
			source_rating.append(score/(len(quote)**(3/15)))
		rating.append(source_rating)
	linear_quotes = []
	linear_rating = []
	#rank the quotes
	for i in xrange(0,len(list_of_quotes)):
		for j in xrange(0,len(list_of_quotes[i])):
			linear_quotes.append(list_of_quotes[i][j])
			linear_rating.append(rating[i][j])
	ranked_quotes = []
	for i in xrange(0,len(linear_quotes)):#finds max value 
		index = linear_rating.index(max(linear_rating))
		ranked_quotes.append(linear_quotes[index])
		linear_quotes.pop(index)
		linear_rating.pop(index)
	return ranked_quotes

#start asking for input for topic of google search
print "Enter your research topic you would like a source for: "
search_term = raw_input()
#next line, finds a list of urls related to research question
some_urls = find_url(search_term)
result_quotes = []
for website in some_urls:
	result_quotes.append(get_page_quotes(website,search_term))
#print all the ranked quotes
try:
	print "\n\n".join([ranked_quotes(result_quotes,some_urls,search_term)[0],' '])
except:
	print "no good sources found"
