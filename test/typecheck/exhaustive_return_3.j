class Main
{
	Void main()
	{
		A a;
		return a.foo();
	}
}

class A
{
	Int a;

	Void foo()
	{
		println(bar());
	}

	String bar()
	{
		println("a");
	}
}
