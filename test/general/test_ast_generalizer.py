"""Unit tests for AstGeneralizer class."""

import unittest
import xml.etree.ElementTree as ET

from transpyle.general.ast_generalizer import \
    ContinueIteration, AstGeneralizer, IdentityAstGeneralizer, XmlAstGeneralizer


class Tests(unittest.TestCase):

    def test_construct_base(self):
        ast_generalizer = AstGeneralizer()
        with self.assertRaises(NotImplementedError):
            ast_generalizer.generalize(None)

        identity_generalizer = IdentityAstGeneralizer()
        self.assertEqual(identity_generalizer.generalize('abcde'), 'abcde')

        xml_generalizer = XmlAstGeneralizer()

    def test_xml_generalizer(self):
        xml_generalizer = XmlAstGeneralizer()

        with self.assertRaises(NotImplementedError):
            xml_generalizer.generalize(ET.Element('abcde'))

        class MyGeneralizer(XmlAstGeneralizer):

            def _some_node(self, node):
                return self.transform_one(ET.Element('test'), warn=True)

            def _other_node(self, node):
                return 'abcde'

        my_generalizer = MyGeneralizer()
        # self.assertEqual(len(my_generalizer._transforms), 2, msg=my_generalizer._transforms)

        with self.assertRaises(ContinueIteration):
            my_generalizer.generalize(ET.Element('some-node'))
        with self.assertRaises(ContinueIteration):
            my_generalizer.generalize(ET.Element('some_node'))

        self.assertEqual(my_generalizer.generalize(ET.Element('other_node')), 'abcde')
