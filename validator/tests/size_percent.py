from test import BaseTest, ValidatorError
import random

class Test_Size_Percent(BaseTest):
    label = 'Size specified by percent'
    level = 1
    category = 3
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            s = random.randint(45,75)
            params = {'size': 'pct:%s' % s}
            img = result.get_image(params)
            self.validationInfo.check('size', img.size, (s*10,s*10), result)

            match = 0
            # Find square size
            sqs = s
            for i in range(5):
                x = random.randint(0,9)
                y = random.randint(0,9)
                xi = x * sqs + 13;
                yi = y * sqs + 13;
                box = (xi,yi,xi+(sqs-13),yi+(sqs-13))
                sqr = img.crop(box)
                ok = self.validationInfo.do_test_square(sqr, x, y, result)
                if ok:
                    match += 1
                else:
                    error = (x,y)      
            if match >= 4:           
                return result
            else:
                raise ValidatorError('color', 1,0, result) 
           
        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            raise