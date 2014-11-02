from test import BaseTest, ValidatorError
import random

class Test_Size_Bwh(BaseTest):
    label = 'Size specified by !w,h'
    level = 2
    category = 3
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            w = random.randint(350,750)
            h = random.randint(350,750)
            s = min(w,h)
            params = {'size': '!%s,%s' % (w,h)}
            img = result.get_image(params)
            self.validationInfo.check('size', img.size, (s,s), result)

            match = 0
            sqs = int(s/1000.0 * 100)
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
            if match >= 3:           
                return result
            else:
                raise ValidatorError('color', 1,0, result) 
               
        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            raise