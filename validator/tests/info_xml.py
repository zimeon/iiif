from test import BaseTest, ValidatorError
from lxml import etree

class Test_Info_Xml(BaseTest):
    label = "Check Image Information (XML)"
    level = 0
    category = 1
    versions = ["1.0"]
    validationInfo = None

    def __init__(self, info):
        self.validationInfo = info

    def run(self, result):      
        url = result.make_info_url('xml')
        try:
            data = result.fetch(url)
        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            self.validationInfo.check('format', result.last_headers['content-type'], ['application/xml', 'text/xml'], result)
            raise
        try:
            dom = etree.XML(data)
        except:
            raise ValidatorError('format', 'XML', 'Unknown', result)

        ns = { 'i':'http://library.stanford.edu/iiif/image-api/ns/'}
        self.validationInfo.check('required-field: /info', len(dom.xpath('/i:info', namespaces=ns)), 1, result)
        self.validationInfo.check('required-field: /info/identifier', len(dom.xpath('/i:info/i:identifier', namespaces=ns)), 1, result)
        self.validationInfo.check('required-field: /info/height', len(dom.xpath('/i:info/i:height', namespaces=ns)), 1, result)
        self.validationInfo.check('required-field: /info/width', len(dom.xpath('/i:info/i:width', namespaces=ns)), 1, result)
        return result