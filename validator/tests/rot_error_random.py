from test import BaseTest

class Test_Rot_Error_Random(BaseTest):
    label = 'Random rotation gives 400'
    level = 1
    category = 4
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            url = result.make_url({'rotation': self.validationInfo.make_randomstring(4)})
            error = result.fetch(url)
            self.validationInfo.check('status', result.last_status, 400, result)
            return result
        except:
            raise