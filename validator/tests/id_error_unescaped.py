from test import BaseTest

class Test_Id_Error_Unescaped(BaseTest):
    label = 'Unescaped identifier gives 400'
    level = 1
    category = 1
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            url = result.make_url({'identifier': '[frob]'})
            url = url.replace('%5B', '[')
            url = url.replace('%5D', ']')
            error = result.fetch(url)
            self.validationInfo.check('status', result.last_status, [400, 404], result)
            return result   
        except:
            raise