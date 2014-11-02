from test import BaseTest

class Test_Id_Basic(BaseTest):
    label = 'Image is returned'
    level = 0
    category = 1
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            url = result.make_url(params={})
            data = result.fetch(url)
            self.validationInfo.check('status', result.last_status, 200, result)
            img = result.make_image(data)
            return result
        except:
            raise