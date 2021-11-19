// 07_support.j

class Main
{
	Void main()
	{
		println(new Foo().foo(420, 69));
		println(new Foo().bar("aaa", "aaa"));
		println(new Foo().bar("aaa", "a"));
		println(new Foo().bar("xxx", "bbb"));
	}
}

class Foo
{
	Int foo(Int x, Int y)
	{
		Int a; Int b; Int c; Int d; Int e; Int f; Int g; Int h;

		a = x / y;
		b = -x / y;
		c = x / -y;
		d = -x / -y;

		println(a);
		println(b);
		println(c);
		println(d);

		return 420;
	}

	Int bar(String a, String b)
	{
		println(a == b);
		println(a != b);

		return 69;
	}
}
