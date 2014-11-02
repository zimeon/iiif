from test import BaseTest
import urllib2

class Test_Format_Conneg(BaseTest):
    label = 'Negotiated format'
    level = 1
    category = 7
    versions = [u'1.0', u'1.1']
    validationInfo = None

    def run(self, result):
        url = result.make_url(params={})
        hdrs = {'Accept': 'image/png;q=1.0'}
        try:
            r = urllib2.Request(url, headers=hdrs)
            wh = urllib2.urlopen(r)
            img = wh.read()   
            wh.close()
        except urllib2.HTTPError, e:
            wh = e
        ct = wh.headers['content-type']
        result.last_url = url
        result.last_headers = wh.headers.dict
        result.last_status = wh.code
        result.urls.append(url)
        self.validationInfo.check('format', ct, 'image/png', result)
        return result