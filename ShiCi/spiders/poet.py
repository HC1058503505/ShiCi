
# -*- coding:utf-8 -*-

import re
import requests
import scrapy
from bs4 import BeautifulSoup
from scrapy.selector import Selector
from scrapy.http import Request
from ShiCi.items import ShiciItem
from ShiCi.items import PoetItem
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
import time
import json

class PoetSpider(scrapy.Spider):
	
	name = 'poet'
	allowed_domains = ['gushiwen.org']
	bash_url = 'https://so.gushiwen.org/authors/'


	# chrome_options = Options()
	# chrome_options.add_argument('--headless')
	# chrome_options.add_argument('--disable-gpu')
	# browser = webdriver.Chrome(chrome_options=chrome_options)

	def start_requests(self):
		yield Request(self.bash_url,self.parse)


	def parse(self, response):
		poet_html = response.text.replace('<br />','/n').replace('<strong>','').replace('</strong>','')

		sright_BS = BeautifulSoup(poet_html, 'lxml')

		sright_div = sright_BS.find('div', class_ = 'sright')
		sright_div_a = sright_div.find_all('a')

		for a in sright_div_a:
			dynasty = a.string
			dynasty_url = 'https://so.gushiwen.org' + a['href']
			yield Request(dynasty_url, self.poetList, meta={'poet_dynasty' : dynasty})

	def poetList(self, response):
		poet_list_html = response.text.replace('<br />','/n').replace('<strong>','').replace('</strong>','')
		poet_list_bs = BeautifulSoup(poet_list_html,'lxml')
		poet_list_div_main3 = poet_list_bs.find('div',class_='main3')
		poet_list_page_div = poet_list_div_main3.find('div',class_='son1')
		poet_list_page_span = poet_list_page_div.find('span')
		page_span_split_list = poet_list_page_span.string.split('/')
		page_span = page_span_split_list[-1]
		page = int(re.findall('\d+',page_span)[0])

		dynasty = response.meta['poet_dynasty']
		for page_num in xrange(1,page+1):
			url = 'https://so.gushiwen.org/authors/Default.aspx?p=' + str(page_num) + '&c=' + dynasty
			yield Request(url,self.poet, meta={'poet_dynasty' : dynasty})

	def poet(self, response):
		poet_html = response.text.replace('<br />','/n').replace('<strong>','').replace('</strong>','')
		poet_bs = BeautifulSoup(poet_html,'lxml')
		poet_bs_son_div = poet_bs.find_all('div',class_='divimg')
		for div in poet_bs_son_div:
			href = div.a['href']
			poet_id_temp = href.split('_')[-1]
			poet_id = poet_id_temp.split('.')[0]
			poet_url = 'https://so.gushiwen.org/' + href
			dynasty = response.meta['poet_dynasty']
			yield Request(poet_url, self.poetDetail, meta={'poet_dynasty' : dynasty, 'poet_id' : poet_id})

	def Test(self, response):
		dynasty = response.meta['poet_dynasty']
		yield Request('https://so.gushiwen.org/authorv_461b461c1542.aspx', self.poetDetail,meta={'poet_dynasty' : dynasty, 'poet_id' : 'Test00000000'})

	def poetDetail(self, response):

		poet_item = PoetItem()

		poet_item['poet_id'] = response.meta['poet_id']
		poet_item['poet_dynasty'] = response.meta['poet_dynasty']

		poet_html = response.text.replace('<br />','/n').replace('<strong>','').replace('</strong>','')
		poet_detail_bs = BeautifulSoup(poet_html, 'lxml')
		# poet_detail_abstract
		poet_detail_abstract = poet_detail_bs.find('div', class_='sonspic')
		poet_detail_abstract_divimg = poet_detail_abstract.find('div',class_='divimg')
		poet_detail_abstract_img = poet_detail_abstract_divimg.find('img')

		poet_portrait = poet_detail_abstract_img['src']
		poet_item['poet_portrait'] = poet_portrait
		poet_name = poet_detail_abstract_img['alt']
		poet_item['poet_name'] = poet_name
		# poet_item['poet_portrait'] = poet_portrait

		poet_detail_abstract_p = poet_detail_abstract.find_all('p')[-1]
		poet_detail_abstract_p.a.decompose()
		poet_item['poet_abstract'] = poet_detail_abstract_p.string

		# poet_detail_extension
		poet_extension = []
		poet_detail_sons = poet_detail_bs.find_all('div', class_ = 'sons')

		for son in poet_detail_sons:
			# print 'son-----------------start'
			# print son
			# print 'son*****************end'
			if son.find('div',class_='contyishang') == None:
				continue

			extension_bs = son

			if son.attrs.has_key('id'):

				son_id = son['id']
				son_identifier = re.findall('\d+',son_id)[0]
				son_type = ''.join(re.findall('[a-zA-Z]',son_id))

				ajax_url = 'https://so.gushiwen.org/authors/ajaxziliao.aspx?id=' + son_identifier
				headers = {'user-agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
				extension_ajax_response = requests.get(ajax_url,headers=headers)
				
				# self.browser.get(ajax_url)
				time.sleep(1)
				# extension_ajax_response = self.browser.page_source
				extension_ajax_text = extension_ajax_response.text.replace('<br />', '/n')
				extension_bs = BeautifulSoup(extension_ajax_text,'lxml')

			
			extension_bs_contyishang = extension_bs.find('div','contyishang')
			# ajax 返回内容为None
			if extension_bs_contyishang == None:
				continue
			else:
				# h2
				extension_bs_h2 = extension_bs_contyishang.find('h2')
				extension_title = extension_bs_h2.get_text()

			dingpai_div = extension_bs.find('div', class_='dingpai')
			if dingpai_div == None:
				extension_good = ''
				extension_bad = ''
			else:
				# dingpai
				dingpai_text = dingpai_div.get_text('|',strip=True).split('|')
				extension_good = re.findall('\d+',dingpai_text[0])[0]
				extension_bad = re.findall('\d+',dingpai_text[1])[0]
			# cankao
			# cankao_div = extension_bs.find('div', class_='cankao')
			
			# if cankao_div != None:
			# 	cankao_div.decompose()

			# extension content
			extension_bs_p_str = ''
			if extension_bs_contyishang != None:
				
				son_extension_p = extension_bs_contyishang.find_all('p')

				if son_extension_p == None or len(son_extension_p) == 0:
					if extension_bs_h2 != None:
						extension_bs_h2.decompose()
						extension_bs_p_str = extension_bs_contyishang.get_text(strip=True)
					else:
						pass
				else:
					for p in son_extension_p:
						if p != son_extension_p[-1]:
							extension_bs_p_str = extension_bs_p_str + p.get_text(strip=True) + '/n'
						else:
							extension_bs_p_str = extension_bs_p_str + p.get_text(strip=True)
			else:
				pass


			temp_extension = {
				'extension_title' : extension_title,
				'extension_good' : extension_good,
				'extension_bad' : extension_bad,
				'extension_content' : extension_bs_p_str
			} 

			poet_extension.append(temp_extension)
				

		poet_item['poet_extension'] = poet_extension

		return poet_item





























		
