## Assignment 1
Ng Zhia Yang, A0204879R

### folder structure
I placed the actual implementations under `src/`, alongside several helper classes and functions. The important files are, as one might expect, `lexer.py`, `parser.py`, and `ast.py`.

The top-level `lex.py` and `parse.py` files are drivers that import the implementation modules and read the input file from the command line, etc. etc. Usage is as specified in the assignment doc, `./lex.py src.j` and `./parse.py src.j` respectively.


### lexer

The lexer is a simple lexer using straightforward matching techniques (not regular expressions). It provides an interface to read one token from the input stream, returning the token and the rest of the stream. Whitespace is consumed before reading a token.

The matching is done with a "longest-token-first" approach, though in reality it just means scanning for the 2-character tokens before the single-character ones. The other tokens (integer literals, string literals, class names, and identifiers) all have uniquely identifying leading characters — `[0-9]`, `"`, `[A-Z]`, and `[a-z]` respectively — so it is no problem to get the correct token.

Wrt. string literals:

1. Decimal escapes are enforced to be exactly 3 characters (so `\65` is invalid, and has to be `\065`), and the escaped value should be at most 127.
2. A similar story for hex escapes, which must be 2 characters (so `\x41`).

Of note, the lexer "standardises" identifiers and classnames, lowercasing all characters other than the first one (to follow the grammar). This will hopefully simplify code in the type checker and further stages.


### parser

The parser is a relatively straightforward recursive descent, operator-precedence (ie. Pratt) parser. The grammar rules are roughly followed, though the function names do not correspond exactly to the production names (it's just what I usually name them).

No backtracking is done; disambiguation is done by a combination of tree-rewriting and deferring the construction of the AST.

Some notes:

1. For the case of `Type ident;` vs `Type ident(...)`, construction of the AST node is deferred till either the `;` or the `(` is seen, requiring no explicit support from the lexer.
2. DotOps and function calls are handled specifically via `parse_atom_chain`, which tries to recursively parse any possible chain of atoms, like `a.b.c().d().e()`.
3. Since expressions are not statements in general, a special `ExprStmt` wrapper is used to wrap a function call to make it a statement



### other stuff

Errors look really nice:
```
test/prog1.j:9:17: error: expected ';' after statement
   | 
 9 |     foozle()
   |             ^
```

Location information is tracked in the lexer, and carried over to the AST nodes by the parser. This will enable (in the future) good error reporting for typechecking/codegen errors.


Also: I'm not sure whether `STRING` as a class name is invalid, since it would, in theory, be identical to `String` under the case-insensitivty rules. For this implementation it is allowed since there is no typechecking yet, but I think in the future it will have to be banned.







