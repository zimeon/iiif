from test import BaseTest, ValidatorError

class Test_Linkheader_Profile(BaseTest):
    label = 'Profile Link Header'
    level = 3
    category = 7
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        url = result.make_url(params={})
        data = result.fetch(url)
        try:
            lh = result.last_headers['link']
        except KeyError:
            raise ValidatorError('profile', '', 'URI', result)
        links = result.parse_links(lh)
        profile = result.get_uri_for_rel(links, 'profile')
        if not profile:
            raise ValidatorError('profile', '', 'URI', result)
        elif result.version == "1.0" and not profile.startswith('http://library.stanford.edu/iiif/image-api/compliance.html'):
            raise ValidatorError('profile', profile, 'URI', result)
        elif result.version == "1.1" and not profile.startswith('http://library.stanford.edu/iiif/image-api/1.1/compliance.html'):
            raise ValidatorError('profile', profile, 'URI', result)
        elif result.version == "2.0" and not profile.startswith('http://iiif.io/api/image/2/'):
            raise ValidatorError('profile', profile, 'URI', result)            
        else:
            result.tests.append('linkheader')
            return result