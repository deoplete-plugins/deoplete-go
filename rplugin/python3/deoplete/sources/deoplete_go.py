import os
import re
import subprocess
import sys

from .base import Base

from deoplete.util import charpos2bytepos
from deoplete.util import error

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ujson_dir = os.path.dirname(current_dir)
    sys.path.insert(0, ujson_dir)
    from ujson import loads
except ImportError:
    from json import loads


class Source(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'go'
        self.mark = '[Go]'
        self.filetypes = ['go']
        self.input_pattern = r'(?:\b[^\W\d]\w*|[\]\)])\.(?:[^\W\d]\w*)?'
        self.rank = 500

        self.gocode_binary = \
            self.vim.vars['deoplete#sources#go#gocode_binary']
        self.package_dot = \
            self.vim.vars['deoplete#sources#go#package_dot']
        self.sort_class = \
            self.vim.vars['deoplete#sources#go#sort_class']
        self.use_cache = \
            self.vim.vars['deoplete#sources#go#use_cache']
        self.json_directory = \
            self.vim.vars['deoplete#sources#go#json_directory']
        self.debug_enabled = \
            self.vim.vars.get('deoplete#sources#go#debug', 0)
        self.cgo = \
            self.vim.vars['deoplete#sources#go#cgo']

        if self.cgo:
            clang_dir = os.path.join(os.path.dirname(current_dir), 'clang')
            sys.path.insert(0, clang_dir)
            import clang.cindex as clang

            self.libclang_path = \
                self.vim.vars.get('deoplete#sources#go#cgo#libclang_path', '')
            self.cgo_std = \
                ['-std',
                 self.vim.vars.get('deoplete#sources#go#cgo#std', 'c11'),
                 '-x', 'c']

            if not clang.Config.loaded:
                clang.Config.set_library_file(self.libclang_path)
                clang.Config.set_compatibility_check(False)

            self.index = clang.Index.create(0)

            self.cgo_cache, self.cgo_headers = dict(), None

    def on_event(self, context):
        if context['event'] == 'BufWinEnter':
            buffer = self.vim.current.buffer
            context['complete_position'] = self.vim.current.window.cursor[1]

            self.get_complete_result(buffer, context)

    def get_complete_position(self, context):
        m = re.search(r'\w*$|(?<=")[./\-\w]*$', context['input'])
        return m.start() if m else -1

    def gather_candidates(self, context):
        buffer = self.vim.current.buffer

        if self.cgo and re.search(r'[^\W\d]*C\.', context['input']):
            if self.cgo_get_include_header(buffer)[0] == 0:
                pass

            elif self.cgo_headers == self.cgo_get_include_header(buffer)[1]:
                return self.cgo_cache[self.cgo_headers]
            else:
                count, self.cgo_headers = self.cgo_get_include_header(buffer)
                return self.cgo_complete(count, self.cgo_headers)

        if self.use_cache:
            import_packages = self.get_import_package(buffer)
            import_package = [x['package'] for x in import_packages]

            m = re.search(r'[\w]*.$', context['input'])
            package = str(m.group(0))
            library = [x['library'][0] for x in import_packages if str(
                package).strip('.') == x['package']]
            if len(library) == 0:
                library = [str(package).strip('.')]
            package_json = os.path.join(
                self.json_directory,
                library[0],
                package + 'json')

            if package not in import_package and \
                    '.' in package and os.path.isfile(package_json):
                with open(package_json) as j:
                    result = loads(j.read())
            else:
                result = self.get_complete_result(buffer, context)

        else:
            result = self.get_complete_result(buffer, context)

        try:
            if result[1][0]['class'] == 'PANIC':
                error(self.vim, 'gocode panicked')
                return []

            if self.sort_class:
                # TODO(zchee): Why not work with this?
                #              class_dict = {}.fromkeys(self.sort_class, [])
                class_dict = {
                    'package': [],
                    'func': [],
                    'type': [],
                    'var': [],
                    'const': [],
                }

            out = []
            sep = ' '

            for complete in result[1]:
                word = complete['name']
                info = complete['type']
                _class = complete['class']
                abbr = str(word + sep + info).replace(' func', '', 1)
                kind = _class

                if _class == 'package' and self.package_dot:
                    word += '.'

                candidates = dict(word=word,
                                  abbr=abbr,
                                  kind=kind,
                                  info=info,
                                  menu=self.mark,
                                  dup=1
                                  )

                if not self.sort_class or _class == 'import':
                    out.append(candidates)
                else:
                    class_dict[_class].append(candidates)

            # append with sort by complete['class']
            if self.sort_class:
                for c in self.sort_class:
                    for x in class_dict[c]:
                        out.append(x)

            return out
        except Exception:
            return []

    def get_complete_result(self, buffer, context):
        line = self.vim.current.window.cursor[0]
        column = context['complete_position']

        offset = self.vim.call('line2byte', line) + \
            charpos2bytepos(self.vim, context['input'][: column],
                            column) - 1
        source = '\n'.join(buffer).encode()

        process = subprocess.Popen([self.find_gocode_binary(),
                                    '-f=json',
                                    'autocomplete',
                                    buffer.name,
                                    str(offset)],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   start_new_session=True)
        process.stdin.write(source)
        stdout_data, stderr_data = process.communicate()
        return loads(stdout_data.decode())

    def get_import_package(self, buffer):
        start = 0
        packages = []

        for line, b in enumerate(buffer):

            if re.match(r'^\s*import \w*|^\s*import \(', b):
                start = line
                continue
            elif re.match(r'\)', b):
                break
            elif line > start:
                package_name = re.sub(r'\t|"', '', b)
                if str(package_name).find(r'/', 0) > 0:
                    full_package_name = str(package_name).split('/', -1)
                    package_name = full_package_name[
                        len(full_package_name) - 1]
                    library = '/'.join(
                        full_package_name[:len(full_package_name) - 1]),

                    packages.append(dict(
                        library=library,
                        package=package_name
                    ))
                else:
                    packages.append(dict(
                        library='none',
                        package=package_name
                    ))
        return packages

    def cgo_get_include_header(self, buffer):
        headers = []
        count = 0

        for b in buffer:
            m = re.search(r'(^#include\s<[^>]+>)$', b)

            if m:
                headers.append(m.group(1))
                count += 1
            elif re.match(r'^\s*import \"C\"', b):
                break

        return (count, '\n'.join(headers))

    def cgo_parse_candidates(self, result):
        completion = {'dup': 1}
        _type = ""
        word = ""
        placeholder = ""

        for chunk in [x for x in result.string if x.spelling]:
            chunk_spelling = chunk.spelling

            if chunk.isKindTypedText():
                word += chunk_spelling
                placeholder += chunk_spelling
                continue

            elif chunk.isKindResultType():
                _type += chunk_spelling
            else:
                placeholder += chunk_spelling

        completion['word'] = word
        completion['abbr'] = completion['info'] = placeholder

        completion['kind'] = ' '.join(
            [(Clang_Index_h.kinds[result.cursorKind]
              if (result.cursorKind in Clang_Index_h.kinds)
              else str(result.cursorKind)), _type])

        return completion

    def cgo_complete(self, count, headers):
        files = [('fake.c', headers + """
char CString() {
}
""")]
        # clang.TranslationUnit
        # PARSE_NONE = 0
        # PARSE_DETAILED_PROCESSING_RECORD = 1
        # PARSE_INCOMPLETE = 2
        # PARSE_PRECOMPILED_PREAMBLE = 4
        # PARSE_CACHE_COMPLETION_RESULTS = 8
        # PARSE_SKIP_FUNCTION_BODIES = 64
        # PARSE_INCLUDE_BRIEF_COMMENTS_IN_CODE_COMPLETION = 128
        options = 15

        tu = self.index.parse('fake.c', self.cgo_std,
                              unsaved_files=files,
                              options=options)

        cr = tu.codeComplete('fake.c',
                             (count + 2), 1,
                             unsaved_files=files,
                             include_macros=False,
                             include_code_patterns=False,
                             include_brief_comments=False)

        self.cgo_cache[headers] = \
            list(map(self.cgo_parse_candidates, cr.results))
        return self.cgo_cache[headers]

    def find_gocode_binary(self):
        try:
            if os.path.isfile(self.gocode_binary):
                return self.gocode_binary
            else:
                raise
        except Exception:
            return self.find_binary_path('gocode')

    def find_binary_path(self, cmd):
        def is_exec(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        fpath, fname = os.path.split(cmd)
        if fpath:
            if is_exec(cmd):
                return cmd
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                binary = os.path.join(path, cmd)
                if is_exec(binary):
                    return binary
        return error(self.vim, 'gocode binary not found')


class Clang_Index_h(object):
    kinds = dict({
        # Declarations
        1:   't',   # CXCursor_UnexposedDecl # A declaration whose specific kind
        # is not exposed via this interface
        2:   'struct',   # CXCursor_StructDecl (A C or C++ struct)
        3:   'union',   # CXCursor_UnionDecl (A C or C++ union)
        4:   'class',   # CXCursor_ClassDecl (A C++ class)
        5:   'enumeration',   # CXCursor_EnumDecl (An enumeration)
        # CXCursor_FieldDecl (A field (in C) or non-static data member
        6:   'member',
        # (in C++) in a struct, union, or C++ class)
        # CXCursor_EnumConstantDecl (An enumerator constant)
        7:   'enumerator constant',
        8:   'function',   # CXCursor_FunctionDecl (A function)
        9:   'variable',   # CXCursor_VarDecl (A variable)
        # CXCursor_ParmDecl (A function or method parameter)
        10:  'method parameter',
        11:  '11',   # CXCursor_ObjCInterfaceDecl (An Objective-C @interface)
        # CXCursor_ObjCCategoryDecl (An Objective-C @interface for a
        12:  '12',
        # category)
        13:  '13',   # CXCursor_ObjCProtocolDecl
        # (An Objective-C @protocol declaration)
        # CXCursor_ObjCPropertyDecl (An Objective-C @property declaration)
        14:  '14',
        15:  '15',   # CXCursor_ObjCIvarDecl (An Objective-C instance variable)
        16:  '16',   # CXCursor_ObjCInstanceMethodDecl
        # (An Objective-C instance method)
        17:  '17',   # CXCursor_ObjCClassMethodDecl
        # (An Objective-C class method)
        18:  '18',   # CXCursor_ObjCImplementationDec
        # (An Objective-C @implementation)
        19:  '19',   # CXCursor_ObjCCategoryImplDecll
        # (An Objective-C @implementation for a category)
        20:  'typedef',   # CXCursor_TypedefDecl (A typedef)
        21:  'class method',   # CXCursor_CXXMethod (A C++ class method)
        22:  'namespace',   # CXCursor_Namespace (A C++ namespace)
        # CXCursor_LinkageSpec (A linkage specification,e.g. Extern "C")
        23:  '23',
        24:  'constructor',   # CXCursor_Constructor (A C++ constructor)
        25:  'destructor',   # CXCursor_Destructor (A C++ destructor)
        # CXCursor_ConversionFunction (A C++ conversion function)
        26:  'conversion function',
        # CXCursor_TemplateTypeParameter (A C++ template type parameter)
        27:  'a',
        # CXCursor_NonTypeTemplateParameter (A C++ non-type template parameter)
        28:  'a',
        # CXCursor_TemplateTemplateParameter (A C++ template template
        # parameter)
        29:  'a',
        # CXCursor_FunctionTemplate (A C++ function template)
        30:  'function template',
        # CXCursor_ClassTemplate (A C++ class template)
        31:  'class template',
        32:  '32',   # CXCursor_ClassTemplatePartialSpecialization
        # (A C++ class template partial specialization)
        # CXCursor_NamespaceAlias (A C++ namespace alias declaration)
        33:  'n',
        # CXCursor_UsingDirective (A C++ using directive)
        34:  'using directive',
        # CXCursor_UsingDeclaration (A C++ using declaration)
        35:  'using declaration',
        # CXCursor_TypeAliasDecl (A C++ alias declaration)
        36:  'alias declaration',
        # CXCursor_ObjCSynthesizeDecl (An Objective-C synthesize definition)
        37:  '37',
        # CXCursor_ObjCDynamicDecl (An Objective-C dynamic definition)
        38:  '38',
        39:  '39',   # CXCursor_CXXAccessSpecifier (An access specifier)

        # References
        40:  '40',   # CXCursor_ObjCSuperClassRef
        41:  '41',   # CXCursor_ObjCProtocolRef
        42:  '42',   # CXCursor_ObjCClassRef
        43:  '43',   # CXCursor_TypeRef
        44:  '44',   # CXCursor_CXXBaseSpecifier
        45:  '45',   # CXCursor_TemplateRef
        # (A reference to a class template, function template, template
        # template parameter, or class template partial
        # specialization)
        # CXCursor_NamespaceRef (A ref to a namespace or namespace alias)
        46:  '46',
        # CXCursor_MemberRef (A reference to a member of a struct, union,
        47:  '47',
        # or class that occurs in some non-expression context,
        # e.g., a designated initializer)
        48:  '48',   # CXCursor_LabelRef (A reference to a labeled statement)
        49:  '49',   # CXCursor_OverloadedDeclRef
        # (A reference to a set of overloaded functions or function
        # templates that has not yet been resolved to a specific
        # function or function template)
        50:  '50',   # CXCursor_VariableRef

        # Error conditions
        # 70:  '70',   # CXCursor_FirstInvalid
        70:  '70',   # CXCursor_InvalidFile
        71:  '71',   # CXCursor_NoDeclFound
        72:   'u',   # CXCursor_NotImplemented
        73:  '73',   # CXCursor_InvalidCode

        # Expressions
        # CXCursor_UnexposedExpr (An expression whose specific kind is
        100: '100',
        # not exposed via this interface)
        # CXCursor_DeclRefExpr (An expression that refers to some value
        101: '101',
        # declaration, such as a function, varible, or
        # enumerator)
        # CXCursor_MemberRefExpr (An expression that refers to a member
        102: '102',
        # of a struct, union, class, Objective-C class, etc)
        103: '103',   # CXCursor_CallExpr (An expression that calls a function)
        # CXCursor_ObjCMessageExpr (An expression that sends a message
        104: '104',
                      # to an Objective-C object or class)
        # CXCursor_BlockExpr (An expression that represents a block
        105: '105',
                      # literal)
        106: '106',   # CXCursor_IntegerLiteral (An integer literal)
        # CXCursor_FloatingLiteral (A floating point number literal)
        107: '107',
        108: '108',   # CXCursor_ImaginaryLiteral (An imaginary number literal)
        109: '109',   # CXCursor_StringLiteral (A string literal)
        110: '110',   # CXCursor_CharacterLiteral (A character literal)
        # CXCursor_ParenExpr (A parenthesized expression, e.g. "(1)")
        111: '111',
        # CXCursor_UnaryOperator (This represents the unary-expression's
        112: '112',
                      # (except sizeof and alignof))
        # CXCursor_ArraySubscriptExpr ([C99 6.5.2.1] Array Subscripting)
        113: '113',
        # CXCursor_BinaryOperator (A builtin binary operation expression
        114: '114',
                      # such as "x + y" or "x <= y")
        # CXCursor_CompoundAssignOperator (Compound assignment such as
        115: '115',
                      # "+=")
        116: '116',   # CXCursor_ConditionalOperator (The ?: ternary operator)
        # CXCursor_CStyleCastExpr (An explicit cast in C (C99 6.5.4) or
        117: '117',
                      # C-style cast in C++ (C++ [expr.cast]), which uses the syntax
                      # (Type)expr)
        118: '118',   # CXCursor_CompoundLiteralExpr ([C99 6.5.2.5])
        # CXCursor_InitListExpr (Describes an C or C++ initializer list)
        119: '119',
        # CXCursor_AddrLabelExpr (The GNU address of label extension,
        120: '120',
                      # representing &&label)
        121: '121',   # CXCursor_StmtExpr (This is the GNU Statement Expression
                      # extension: ({int X=4; X;})
        # CXCursor_GenericSelectionExpr (brief Represents a C11 generic
        122: '122',
                      # selection)
        # CXCursor_GNUNullExpr (Implements the GNU __null extension)
        123: '123',
        # CXCursor_CXXStaticCastExpr (C++'s static_cast<> expression)
        124: '124',
        # CXCursor_CXXDynamicCastExpr (C++'s dynamic_cast<> expression)
        125: '125',
        # CXCursor_CXXReinterpretCastExpr (C++'s reinterpret_cast<>
        126: '126',
                      # expression)
        # CXCursor_CXXConstCastExpr (C++'s const_cast<> expression)
        127: '127',
        # CXCursor_CXXFunctionalCastExpr (Represents an explicit C++ type
        128: '128',
                      # conversion that uses "functional" notion
                      # (C++ [expr.type.conv]))
        129: '129',   # CXCursor_CXXTypeidExpr (A C++ typeid expression
                      # (C++ [expr.typeid]))
        # CXCursor_CXXBoolLiteralExpr (brief [C++ 2.13.5] C++ Boolean
        130: '130',
                      # Literal)
        # CXCursor_CXXNullPtrLiteralExpr ([C++0x 2.14.7] C++ Pointer
        131: '131',
                      # Literal)
        # CXCursor_CXXThisExpr (Represents the "this" expression in C+)
        132: '132',
        133: '133',   # CXCursor_CXXThrowExpr ([C++ 15] C++ Throw Expression)
        # CXCursor_CXXNewExpr (A new expression for memory allocation
        134: '134',
                      # and constructor calls)
        135: '135',   # CXCursor_CXXDeleteExpr (A delete expression for memory
                      # deallocation and destructor calls)
        136: '136',   # CXCursor_UnaryExpr (A unary expression)
        # CXCursor_ObjCStringLiteral (An Objective-C string literal
        137: '137',
                      # i.e. @"foo")
        # CXCursor_ObjCEncodeExpr (An Objective-C @encode expression)
        138: '138',
        # CXCursor_ObjCSelectorExpr (An Objective-C @selector expression)
        139: '139',
        # CXCursor_ObjCProtocolExpr (An Objective-C @protocol expression)
        140: '140',
        # CXCursor_ObjCBridgedCastExpr (An Objective-C "bridged" cast
        141: '141',
                      # expression, which casts between Objective-C pointers and C
                      # pointers, transferring ownership in the process)
        # CXCursor_PackExpansionExpr (Represents a C++0x pack expansion
        142: '142',
                      # that produces a sequence of expressions)
        # CXCursor_SizeOfPackExpr (Represents an expression that computes
        143: '143',
                      # the length of a parameter pack)
        # CXCursor_LambdaExpr (Represents a C++ lambda expression that
        144: '144',
                      # produces a local function object)
        # CXCursor_ObjCBoolLiteralExpr (Objective-c Boolean Literal)
        145: '145',

        # Statements
        # CXCursor_UnexposedStmt (A statement whose specific kind is not
        200: '200',
                      # exposed via this interface)
        201: '201',   # CXCursor_LabelStmt (A labelled statement in a function)
        202: '202',   # CXCursor_CompoundStmt (A group of statements like
                      # { stmt stmt }.
        203: '203',   # CXCursor_CaseStmt (A case statment)
        204: '204',   # CXCursor_DefaultStmt (A default statement)
        205: '205',   # CXCursor_IfStmt (An if statemen)
        206: '206',   # CXCursor_SwitchStmt (A switch statement)
        207: '207',   # CXCursor_WhileStmt (A while statement)
        208: '208',   # CXCursor_DoStmt (A do statement)
        209: '209',   # CXCursor_ForStmt (A for statement)
        210: '210',   # CXCursor_GotoStmt (A goto statement)
        211: '211',   # CXCursor_IndirectGotoStmt (An indirect goto statement)
        212: '212',   # CXCursor_ContinueStmt (A continue statement)
        213: '213',   # CXCursor_BreakStmt (A break statement)
        214: '214',   # CXCursor_ReturnStmt (A return statement)
        # CXCursor_GCCAsmStmt (A GCC inline assembly statement extension)
        215: '215',
        # CXCursor_ObjCAtTryStmt (Objective-C's overall try-catch-finally
        216: '216',
                      # statement.
        # CXCursor_ObjCAtCatchStmt (Objective-C's catch statement)
        217: '217',
        # CXCursor_ObjCAtFinallyStmt (Objective-C's finally statement)
        218: '218',
        # CXCursor_ObjCAtThrowStmt (Objective-C's throw statement)
        219: '219',
        # CXCursor_ObjCAtSynchronizedStmt (Objective-C's synchronized
        220: '220',
                      # statement)
        # CXCursor_ObjCAutoreleasePoolStmt (Objective-C's autorelease
        221: '221',
                      # pool statement)
        # CXCursor_ObjCForCollectionStmt (Objective-C's collection
        222: '222',
                      # statement)
        223: '223',   # CXCursor_CXXCatchStmt (C++'s catch statement)
        224: '224',   # CXCursor_CXXTryStmt (C++'s try statement)
        225: '225',   # CXCursor_CXXForRangeStmt (C++'s for (*: *) statement)
        # CXCursor_SEHTryStmt (Windows Structured Exception Handling's
        226: '226',
                      # try statement)
        # CXCursor_SEHExceptStmt (Windows Structured Exception Handling's
        227: '227',
                      # except statement.
        228: '228',   # CXCursor_SEHFinallyStmt (Windows Structured Exception
                      # Handling's finally statement)
        # CXCursor_MSAsmStmt (A MS inline assembly statement extension)
        229: '229',
        230: '230',   # CXCursor_NullStmt (The null satement ";": C99 6.8.3p3)
        # CXCursor_DeclStmt (Adaptor class for mixing declarations with
        231: '231',
                      # statements and expressions)

        # Translation unit
        300: '300',   # CXCursor_TranslationUnit (Cursor that represents the
                      # translation unit itself)

        # Attributes
        # CXCursor_UnexposedAttr (An attribute whose specific kind is
        400: '400',
                      # not exposed via this interface)
        401: '401',   # CXCursor_IBActionAttr
        402: '402',   # CXCursor_IBOutletAttr
        403: '403',   # CXCursor_IBOutletCollectionAttr
        404: '404',   # CXCursor_CXXFinalAttr
        405: '405',   # CXCursor_CXXOverrideAttr
        406: '406',   # CXCursor_AnnotateAttr
        407: '407',   # CXCursor_AsmLabelAttr

        # Preprocessing
        500: '500',   # CXCursor_PreprocessingDirective
        501:   'd',   # CXCursor_MacroDefinition
        502: '502',   # CXCursor_MacroInstantiation
        503: '503',   # CXCursor_InclusionDirective

        # Modules
        600: '600',   # CXCursor_ModuleImportDecl (A module import declaration)
    })
