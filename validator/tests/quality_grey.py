from test import BaseTest

class Test_Quality_Grey(BaseTest):
    label = 'Gray/Grey quality'
    level = 2
    category = 5
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            params = {'quality': 'grey'}
            img = result.get_image(params)
            # self.validationInfo.check('quality', img.mode, 'L', result)

            cols = img.getcolors()
            if img.mode == 1:
                return self.validationInfo.check('quality', 1, 0, result)
            elif img.mode == 'L':
                return self.validationInfo.check('quality', 1, 1, result)
            else:
                # check vast majority of px are triples with v similar r,g,b
                ttl = 0
                for c in cols:
                    if (abs(c[1][0] - c[1][1]) < 5 and abs(c[1][1] - c[1][2]) < 5):
                        ttl += c[0]
                if ttl > 650000:
                    return self.validationInfo.check('quality', 1,1, result)
                else:
                    return self.validationInfo.check('quality', 1,0, result)

            return result
        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            raise