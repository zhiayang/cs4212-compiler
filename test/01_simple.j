// 01_simple.j

class Main
{
	Void main()
	{
		Foo f;

		println("hello, world!" + null);
		f = new Foo().bar().bar().bar();

		println(f.f1);
	}
}

class Foo
{
	Int f1;
	Foo bar()
	{
		if(f1 == 0) { f1 = 1; }
		else        { f1 = f1 * 2; }

		println("you should see this 3 times");
		return this;
	}
}

