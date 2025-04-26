import { NextResponse } from "next/server";
import { currentUser } from "@clerk/nextjs";

export async function GET() {
  const user = await currentUser();
  
  if (!user) {
    return NextResponse.redirect(new URL('/sign-in', process.env.NEXT_PUBLIC_APP_URL));
  }

  return NextResponse.redirect(new URL('/', process.env.NEXT_PUBLIC_APP_URL));
}