class UWU
{
	Void main()
	{
		Int i1;
		Int i2;
		Int i3;
		Int i4;
		Bool b;
		String s;
		A a;

		// assigns
		i1 = 69 + 420;
		i2 = i1 + i2;
		i3 = i1 + i1 + i1 + i1 + 69420;
		i4 = i1;
		b = false && true || false;
		s = "a" + "b";
		s = "a" + s;
		s = null;
		s = "1 + 2" + s + "3 + 4";

		a = new A();
		a = null;
		new A().foo(69);

		return;

		i4 = 1 + 2;
	}
}

class A
{
	A a;
	Int i1;
	Int i2;
	String s1;

	Void foo(Int x)
	{
		// (implicit) field access
		a = null;
		a = new A();

		i1 = x + i2;
		a.i1 = i1;
		i2 = a.i2;

		// explicit field access
		this.i1 = i1;
		this.i2 = i2;

		// lots of chaining
		println(a.a().a().a().a().a().a().a().bar());

		// assignments
		a.a().a().a().a().a().i1 = 69;
		this.i1 = 420;
	}

	Int bar()
	{
		return 69;
	}

	A a()
	{
		return a;
	}
}
