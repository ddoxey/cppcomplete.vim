#!/usr/bin/env python3

from cppcomplete import CPPComplete
import os
import unittest
from tempfile import NamedTemporaryFile


class CPPArtifact:

    others = []

    def __init__(self, suffix, text):
        self.file = NamedTemporaryFile(delete=False, suffix=f'.{suffix}')
        self.file.write(text.strip().encode('UTF-8'))
        self.file.close()

    def __del__(self):
        os.remove(self.file.name)
        for other in self.others:
            if os.path.exists(other):
                os.remove(other)

    def touch(self, ext):
        other = os.path.splitext(self.file.name)[0] + f'.{ext}'
        open(other, 'a').close()
        self.others.append(other)
        return os.path.basename(other)

    @property
    def filename(self):
        return self.file.name

    @property
    def basename(self):
        return os.path.basename(self.file.name)


class TestCPPCompleteGetObjectClassname(unittest.TestCase):

    def test_basic_declaration_a(self):

        sample_cpp = CPPArtifact('cpp', "std::string foobar;")

        classname = CPPComplete.get_object_classname(sample_cpp.filename, 1, "foobar")

        self.assertEqual(classname, 'std::string')


    def test_basic_declaration_b(self):

        sample_cpp = CPPArtifact('cpp', "auto foobar = std::string(\"\");")

        classname = CPPComplete.get_object_classname(sample_cpp.filename, 1, "foobar")

        self.assertEqual(classname, 'std::string')


    def test_copy(self):

        sample_cpp = CPPArtifact('cpp',
        """
            std::string foo;
            auto bar = foo;
        """)

        classname = CPPComplete.get_object_classname(sample_cpp.filename, 2, "bar")

        self.assertEqual(classname, 'std::string')


    def test_local_function_return(self):

        sample_cpp = CPPArtifact('cpp',
        """
            std::string foo();
            auto bar = foo();
        """)

        classname = CPPComplete.get_object_classname(sample_cpp.filename, 2, "bar")

        self.assertEqual(classname, 'std::string')


    def test_include_function_return_a(self):

        sample_hpp = CPPArtifact('hpp',
        """
            std::string foo();
        """)

        sample_cpp = CPPArtifact('cpp',
        """
            #include "{}"
            auto bar = foo();
        """.format(sample_hpp.basename))

        classname = CPPComplete.get_object_classname(sample_cpp.filename, 2, "bar")

        self.assertEqual(classname, 'std::string')


    def test_include_function_return_b(self):

        definition_cpp = CPPArtifact('cpp',
        """
            std::string foo() { return "bar" };
        """)

        hpp_basename = definition_cpp.touch('hpp')

        sample_cpp = CPPArtifact('cpp',
        """
            #include "{}"
            auto bar = foo();
        """.format(hpp_basename))

        classname = CPPComplete.get_object_classname(sample_cpp.filename, 2, "bar")

        self.assertEqual(classname, 'std::string')


    def test_using_namespace_a(self):

        sample_cpp = CPPArtifact('cpp',
        """
            using std;

            string foobar;
        """)

        classname = CPPComplete.get_object_classname(sample_cpp.filename, 3, "foobar")

        self.assertEqual(classname, 'std::string')


    def test_class_member_a(self):

        class_hpp = CPPArtifact('hpp',
        """
            class a {
              public:
                std::string foo("bar");
            }
        """)

        sample_cpp = CPPArtifact('cpp',
        """
            #include "{}"
            a x;
            auto bar = x.foo;
        """.format(class_hpp.basename))

        classname = CPPComplete.get_object_classname(sample_cpp.filename, 3, "bar")

        self.assertEqual(classname, 'std::string')


if __name__ == '__main__':
    unittest.main()
