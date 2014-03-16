#!/usr/bin/python
# -*- coding: utf-8  -*-

"""Unit test for textrange_parser
"""

import unittest
import test_utils

import testSamples
import templateparser

# Main test class
class TemplateParserTestCase(unittest.TestCase):

    def setUp(self):
        self.simple_template = '{{template_name |key1 = value1 |key2 = value2}}'
        self.nested_template = u"""
        
        Cras suscipit lorem eget elit pulvinar et molestie magna tempus.
        Vestibulum.
        {{Toplevel template 
        | key1                = value1
        | key2                = [[File:Al3+.svg|40px|Aluminiumion]] {{nested template 
          | nested_key1 = nested_value1
          | nested_key2 = nested_value2
          }}
        | key3                = value3 
        }} and more text
        """

    def test_parse_template_test_1(self):
        template = templateparser.parse_template( testSamples.Kaliumpermanganat_rev73384760, 'Infobox Chemikalie')
        self.assertEqual(len( template.parameters ), 19)
        self.assertEqual(template.parameters['Aggregat'], u'fest<ref name="GESTIS">{{GESTIS|Name=Kaliumpermanganat|CAS=7722-64-7|Datum=15. Dezember 2007}}</ref>')
        self.assertEqual(template.parameters['Strukturformel'], u'[[Datei:K+.svg|20px|Kaliumion]] [[Datei:Permanganat-Ion2.svg|100px|Permanganation]]')

    def test_parse_template_test_2(self):
        template = templateparser.parse_template( testSamples.Aluminiumnitrat_rev69770393, 'Infobox Chemikalie')
        self.assertEqual(len( template.parameters ), 18)
        self.assertEqual(template.parameters['Aggregat'], u'fest')
        self.assertEqual(template.parameters['Strukturformel'], u'[[Datei:Al3+.svg|40px|Aluminiumion]] <math>\\mathrm{ \\ \\Biggl[}</math> [[Datei:Nitrat-Ion.svg|70px|Nitration]]<math>\\mathrm{ \\ \\!\\ \\Biggr]_3^{-}}</math>')

    def test_parse_template_test_3(self):
        #here we test a page with many inner comments
        template = templateparser.parse_template( testSamples.Ubichinon10_rev73998553, 'Infobox Chemikalie')
        self.assertEqual(len( template.parameters ), 18)
        self.assertEqual(template.parameters['Aggregat'], u'fest')
        self.assertEqual(template.parameters['MAK'], u'<!-- ml·m<sup>−3</sup>, mg·m<sup>−3</sup> -->')
        self.assertEqual(template.parameters['Strukturformel'], u'[[Datei:CoenzymeQ10.svg|200px|Strukturformel von Coenzym Q10]]')

    def test_parse_template_test_4(self):
        #here we test a page with many inner nowiki statements
        template = templateparser.parse_template( testSamples.Butylscopolaminbromid_rev69501497, 'Infobox Chemikalie')
        self.assertEqual(24, len( template.parameters ))
        self.assertEqual(u'{{S-Sätze|25|46}}', template.parameters['S'])

    def test_parse_template_test_local(self):
        sample = testSamples.test_sample1
        template = templateparser.parse_template( sample, 'Infobox Chemikalie')
        self.assertEqual(3, len( template.parameters ))
        self.assertEqual(u'Aluminiumnitrat', template.parameters['Name'])

    def test_nested_template(self):
        nested_template = self.nested_template
        # First fetch the outer template and assert that we get key1 through 3
        template = templateparser.parse_template(nested_template, 'Toplevel template')
        expected = u'[[File:Al3+.svg|40px|Aluminiumion]] {{nested template \n          | nested_key1 = nested_value1\n          | nested_key2 = nested_value2\n          }}'
        self.assertEqual( len(template.parameters.keys()), 3) 
        self.assertEqual( template.parameters['key1'], 'value1' )
        self.assertEqual( template.parameters['key3'], 'value3' )
        self.assertEqual( template.parameters['key2'], expected)
        self.assertEqual( template.start, 111 )
        self.assertEqual( template.end, 401 )
        self.assertFalse(template.parameters.has_key('nested_key1'))
        #
        # Now fetch the inner (nested) template and assert that we get nested_key 1 and 2
        template = templateparser.parse_template(nested_template, 'nested template')
        self.assertEqual( len(template.parameters.keys()), 2) 
        self.assertEqual( template.parameters['nested_key1'], 'nested_value1' )
        self.assertEqual( template.parameters['nested_key2'], 'nested_value2' )
        self.assertEqual( template.start, 239 )
        self.assertEqual( template.end, 350 )

    def test_all_templates(self):
        text = self.nested_template + self.simple_template 
        templates = templateparser.get_all_templates(text)
        self.assertEqual(templates[0].template_name, 'Toplevel template')
        self.assertEqual( len(templates[0].parameters.keys()), 3) 
        self.assertEqual(templates[1].template_name, 'nested template')
        self.assertEqual( len(templates[1].parameters.keys()), 2) 
        self.assertEqual(templates[2].template_name, 'template_name')
        self.assertEqual( len(templates[2].parameters.keys()), 2)
        self.assertEqual( templates[2].parameters_order, ['key1', 'key2'])

    def test_unnamed_parameters(self):
        text = self.nested_template + self.simple_template 
        text = 'Ipsum {{template_name | value1 | value2}} Lorem'
        template = templateparser.parse_template(text,template_name='template_name')
        self.assertEqual( len(template.parameters.keys()), 2)
        self.assertEqual( template.parameters_order, ['parameter_0', 'parameter_1'])
        self.assertEqual( template.parameters['parameter_0'], 'value1')
        self.assertEqual( template.parameters['parameter_1'], 'value2')

    def test_to_wikitext(self):
        template = templateparser.parse_template(self.simple_template, 'template_name')
        self.assertEqual('{{template_name\n | key1 = value1\n | key2 = value2\n}}', template.to_wikitext() )

    def test_without_parameters(self):
        template = templateparser.parse_template('{{FrS}}', start=0, allowEmpty = True)
        self.assertEqual(template.parameters, {} )

    def test_add_parameter(self):
        template = templateparser.parse_template(self.simple_template, 'template_name')
        template.add_parameter('new_param')
        template.set_parameter('new_param', 'new_value')
        self.assertEqual('{{template_name\n | key1 = value1\n | key2 = value2\n | new_param = new_value\n}}', template.to_wikitext() )

    def test_add_parameter_before_after(self):
        template = templateparser.parse_template(self.simple_template, 'template_name')
        template.add_parameter('new_param', before="key1")
        template.set_parameter('new_param', 'new_value')
        self.assertEqual('{{template_name\n | new_param = new_value\n | key1 = value1\n | key2 = value2\n}}', template.to_wikitext() )
        template = templateparser.parse_template(self.simple_template, 'template_name')
        template.add_parameter('new_param', after="key1")
        template.set_parameter('new_param', 'new_value')
        self.assertEqual('{{template_name\n | key1 = value1\n | new_param = new_value\n | key2 = value2\n}}', template.to_wikitext() )

if __name__ == "__main__":
    unittest.main()
