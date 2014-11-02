from test import BaseTest

class Test_Cors(BaseTest):
    label = 'Cross Origin Headers'
    level = 1
    category = 7
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        info = result.get_info();
        cors = result.last_headers.get('access-control-allow-origin', '')
        self.validationInfo.check('CORS', cors, '*', result)
        return result