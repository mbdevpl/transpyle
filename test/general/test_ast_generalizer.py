"""Unit tests for AstGeneralizer class."""

import unittest
import xml.etree.ElementTree as ET

from transpyle.general.ast_generalizer import \
    ContinueIteration, AstGeneralizer, IdentityAstGeneralizer, XmlAstGeneralizer


class Tests(unittest.TestCase):

    def test_base_construct(self):
        ast_generalizer = AstGeneralizer()
        with self.assertRaises(NotImplementedError):
            ast_generalizer.generalize(None)

    def test_identity_construct(self):
        identity_generalizer = IdentityAstGeneralizer()
        self.assertEqual(identity_generalizer.generalize('abcde'), 'abcde')

    def test_xml_construct(self):
        xml_generalizer = XmlAstGeneralizer()

        with self.assertRaises(NotImplementedError):
            xml_generalizer.generalize(ET.Element('abcde'))

        class MyGeneralizer(XmlAstGeneralizer):  # pylint: disable=missing-docstring

            def _some_node(self, _):
                return self.transform_one(ET.Element('test'), warn=True)

            def _other_node(self, _):
                return 'abcde'

        my_generalizer = MyGeneralizer()
        # self.assertEqual(len(my_generalizer._transforms), 2, msg=my_generalizer._transforms)

        with self.assertRaises(ContinueIteration):
            my_generalizer.generalize(ET.Element('some-node'))
        with self.assertRaises(ContinueIteration):
            my_generalizer.generalize(ET.Element('some_node'))

        self.assertEqual(my_generalizer.generalize(ET.Element('other_node')), 'abcde')

    def test_xml_get(self):
        xml_generalizer = XmlAstGeneralizer()
        with self.assertRaises(SyntaxError):
            xml_generalizer.get_one(ET.Element('some-node'), './xpath')

        empty = xml_generalizer.get_all(ET.Element('some-node'), './xpath', require_results=False)
        self.assertListEqual(empty, [])

        with self.assertRaises(SyntaxError):
            xml_generalizer.get_all(ET.Element('some-node'), './xpath')

    def test_xml_transform(self):
        xml_generalizer = XmlAstGeneralizer()
        with self.assertRaises(NotImplementedError):
            xml_generalizer.transform_one(ET.Element('some-node'))
        with self.assertRaises(NotImplementedError):
            xml_generalizer.transform_all([ET.Element('some-node')])

        empty = xml_generalizer.transform_all_subnodes(ET.Element('some-node'))
        self.assertListEqual(empty, [])
