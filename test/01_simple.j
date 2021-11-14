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
		Int k;
		k = 3 * x + y;
		// if(k == 1) { return x; } else { return k; }
		return k;
	}
}
