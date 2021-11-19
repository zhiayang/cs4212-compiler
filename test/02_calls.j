// 02_calls.j

class Main
{
	Void main()
	{
		// maximum spillage
		println(new Foo().x());
	}
}

class Foo
{
Int x()                                                                        { return x(1); }
Int x(Int a)                                                                   { return x(a,2); }
Int x(Int a,Int b)                                                             { return x(a,b,3); }
Int x(Int a,Int b,Int c)                                                       { return x(a,b,c,4); }
Int x(Int a,Int b,Int c,Int d)                                                 { return x(a,b,c,d,5); }
Int x(Int a,Int b,Int c,Int d,Int e)                                           { return x(a,b,c,d,e,6); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f)                                     { return x(a,b,c,d,e,f,7); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g)                               { return x(a,b,c,d,e,f,g,8); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h)                         { return x(a,b,c,d,e,f,g,h,9); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i)                   { return x(a,b,c,d,e,f,g,h,i,10); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j)             { return x(a,b,c,d,e,f,g,h,i,j,11); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k)       { return x(a,b,c,d,e,f,g,h,i,j,k,12); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l) { return x(a,b,c,d,e,f,g,h,i,j,k,l,13); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l,Int m)
{
	println(m); println(l); println(k); println(j); println(i); println(h);
	println(g); println(f); println(e); println(d); println(c); println(b); println(a);
	return 0;
}

}
