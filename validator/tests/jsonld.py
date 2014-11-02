from test import BaseTest
import urllib2

class Test_Jsonld(BaseTest):
    label = 'JSON-LD Media Type'
    level = 1
    category = 7
    versions = [u'2.0']
    validationInfo = None

    def run(self, result):
        url = result.make_info_url()
        hdrs = {'Accept': 'application/ld+json'}
        try:
            r = urllib2.Request(url, headers=hdrs)
            wh = urllib2.urlopen(r)
            img = wh.read()   
            wh.close()
        except urllib2.HTTPError, e:
            wh = e
        ct = wh.headers['content-type']
        self.validationInfo.check('json-ld', ct, 'application/ld+json', result)
        return result