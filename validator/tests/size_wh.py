from test import BaseTest, ValidatorError
import random

class Test_Size_Wh(BaseTest):
    label = 'Size specified by w,h'
    level = 2
    category = 3
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            w = random.randint(350,750)
            h = random.randint(350,750)
            params = {'size': '%s,%s' % (w,h)}
            img = result.get_image(params)
            self.validationInfo.check('size', img.size, (w,h), result)

            match = 0
            sqsw = int(w/1000.0 * 100)
            sqsh = int(h/1000.0 * 100)
            for i in range(5):
                x = random.randint(0,9)
                y = random.randint(0,9)
                xi = x * sqsw + 13;
                yi = y * sqsh + 13;
                box = (xi,yi,xi+(sqsw-13),yi+(sqsh-13))
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