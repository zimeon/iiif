from test import BaseTest, ValidatorError
import random

class Test_Id_Squares(BaseTest):
    label = 'Correct image returned'
    level = 0
    category = 1
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            url = result.make_url({'format':'jpg'})
            data = result.fetch(url)
            self.validationInfo.check('status', result.last_status, 200, result)            
            img = result.make_image(data) 
            # Now test some squares for correct color

            match = 0
            for i in range(5):
                x = random.randint(0,9)
                y = random.randint(0,9)
                xi = x * 100 + 13;
                yi = y * 100 + 13;
                box = (xi,yi,xi+74,yi+74)
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
            raise