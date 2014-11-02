from test import BaseTest

class Test_Region_Error_Random(BaseTest):
    label = 'Random region gives 400'
    level = 1
    category = 2
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            url = result.make_url({'region': self.validationInfo.make_randomstring(6)})
            error = result.fetch(url)
            self.validationInfo.check('status', result.last_status, 400, result)
            return result          
        except:
            # self.validationInfo.check('status', result.last_status, 200)
            raise