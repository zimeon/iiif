from test import BaseTest, ValidatorError
import random

class Test_Region_Percent(BaseTest):
    label = 'Region specified by percent'
    level = 2
    category = 2
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            match = 0
            for i in range(5):
                x = random.randint(0,9)
                y = random.randint(0,9)
                params = {'region' : 'pct:%s,%s,9,9' % (x*10+1, y*10+1)}
                img = result.get_image(params)                           
                ok = self.validationInfo.do_test_square(img,x,y, result)
                if ok:
                    match += 1
            if match >= 4:         
                return result
            else:
                raise ValidatorError('color', 1,0, result)
        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            raise