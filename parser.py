import bs4

class Query:
    '''Represents a search query with its components: number, title, description, and narrative.'''
    def __init__(self, num, title, desc, narr):
        self.num = num
        self.title = title
        self.desc = desc
        self.narr = narr

    def merge_all(self):
        return " ".join([self.title, self.narr, self.desc])
    
class Document:
    '''Represents a document with its metadata and content.'''
    def __init__(self, doc_id, doc_no, date, title, heading_lst, geography_lst, text_lst):
        self.doc_id = doc_id
        self.doc_no = doc_no

        self.date = date
        self.title = title
        self.heading_lst = heading_lst
        self.geography_lst = geography_lst
        self.text_lst = text_lst
    
    def merge_all(self):
        return " ".join([self.title] + self.heading_lst + self.geography_lst + self.text_lst)


def get_file_content(file_path):
    '''Reads the content of a file and returns it as a string.'''
    with open(file_path, 'r') as file:
        content = file.read()
    return content

def parse_topics(topics_file):
    '''Parses the topics XML file and yields Query objects.'''

    soup = bs4.BeautifulSoup(get_file_content(topics_file), 'xml')

    for top in soup.find_all('top'):
        num = top.num.text.strip()
        title = top.title.text.strip()
        desc = top.desc.text.strip()
        narr = top.narr.text.strip()
    
        query = Query(num, title, desc, narr)
        yield query


def parse_document_cs(doc: bs4.element.Tag):
    '''Parses a Czech document from the XML structure and returns a Document object.'''

    doc_id = doc.find('DOCID').text.strip()
    doc_no = doc.find('DOCNO').text.strip()
    date = doc.find('DATE').text.strip()

    title = doc.find('TITLE')
    title = title.text.strip() if title else ""
    
    heading_lst = []
    for heading in doc.find_all('HEADING'):
        heading_lst.append(heading.text.strip())
    
    geography_lst = []
    for geography in doc.find_all('GEOGRAPHY'):
        geography = geography.text.strip()
        geography_lst.append(geography)
    
    text_lst = []
    for text in doc.find_all('TEXT'):
        text = text.text.strip()
        text_lst.append(text)
    
    document = Document(doc_id, doc_no, date, title, heading_lst, geography_lst, text_lst)
    return document

def parse_document_en(doc: bs4.element.Tag):
    '''Parses an English document from the XML structure and returns a Document object.'''

    # Exclude metadata fields that are not relevant
    exclude_tags = {'JP', 'ID', 'IS', 'SL', 'SP', 'SM', 'PR', 'NA', 'HI', 'CR', 'CO',
        'NO', 'PF', 'IN', 'WD', 'EI', 'TM', 'BR', 'DK', 'CB', 'SN', 'PD', 'PN', 'PG',
        'CN', 'PP', 'SE', 'FN', 'AN', 'GO', 'TI', 'RS', 'WS', 'UP', 'CX','CI', 'SI',
        'PY', 'PH', 'CF', 'GT', 'CP', 'BD', 'ED', 'PT', 'AU', 'DP', 'DL'}
    

    # Useful tags for parsing:
    
    # <TE>    - Text: The main body paragraphs of the article.
    # <LD>    - Lead Paragraph(s): The opening paragraph(s) of the story.
    # <DF>    - Descriptor Fact: Specific entities, names, or figures tagged for search.
    # <DC>    - Descriptor Concept: Subject keywords or broad tags for database searching.    
    # <DH>    - Deck Heading: The subheadline or summary sentence below the main headline.
    # <KH>    - Kicker Heading: A smaller headline that goes above the main headline.
    

    doc_id = doc.find('DOCID').text.strip()
    doc_no = doc.find('DOCNO').text.strip()

    date = doc.find('DD').text.strip() # Display Date: Reader-friendly formatted date
    title = doc.find('HD').text.strip() # Headline: The main title of the article.

    exclude_tags = exclude_tags.union({'HD', 'DD', 'DOCID', 'DOCNO'})
    
    text_lst = []
    for child in doc.find_all(recursive=False):
        if child.name not in exclude_tags and child.text:
            text_lst.append(child.text.strip())

    document = Document(doc_id, doc_no, date, title, [], [], text_lst)

    return document

def go_through_file(doc_path, language):
    '''Reads an XML document file, parses its content based on the specified language, and yields Document objects.'''

    soup = bs4.BeautifulSoup(get_file_content(doc_path), 'xml')
    for doc in soup.find_all('DOC'):
        if language == 'cs':
            parsed_doc = parse_document_cs(doc)
        elif language == 'en':
            parsed_doc = parse_document_en(doc)
        
        yield parsed_doc
