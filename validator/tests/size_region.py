from test import BaseTest, ValidatorError
import random

class Test_Size_Region(BaseTest):
    label = 'Region at specified size'
    level = 1
    category = 3
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            # ask for a random region, at a random size < 100
            for i in range(5):
                s = random.randint(35,90)
                x = random.randint(0,9)
                y = random.randint(0,9)
                params = {'size': '%s,%s' % (s,s)}
                params['region'] = '%s,%s,100,100' % (x*100, y*100)
                img = result.get_image(params)
                if img.size != (s,s):
                    raise ValidatorError('size', img.size, (s,s), result)        
                ok = self.validationInfo.do_test_square(img,x,y, result)
                if not ok:
                    raise ValidatorError('color', 1, self.validationInfo.colorInfo[0][0], result)            
            return result
        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            raise