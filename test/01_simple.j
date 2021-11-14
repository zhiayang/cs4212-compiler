class Main
{
	Void main()
	{
		Foo foo;
		foo.foo(69, 420);
	}
}

class Foo
{
	Int foo(Int x, Int y)
	{
		return 2 * x + y;
	}
}