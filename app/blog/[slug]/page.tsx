import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { formatDate, getPost, site } from "@/lib/content";
import { Media } from "@/components/Media";

type Props = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return site.blog.map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const post = getPost((await params).slug);
  return post ? { title: post.title, description: post.excerpt } : {};
}

export default async function PostPage({ params }: Props) {
  const post = getPost((await params).slug);
  if (!post) notFound();

  return (
    <article className="section">
      <div className="container container--narrow">
        <Link href="/blog" className="text-link">
          <span aria-hidden="true">←</span> All stories
        </Link>
        <h1 className="mt-sm">{post.title}</h1>
        <p className="meta">
          <time dateTime={post.date}>{formatDate(post.date)}</time> · {post.author}
          {post.tags?.length ? ` · ${post.tags.join(", ")}` : ""}
        </p>
        <Media src={post.image} alt={post.imageAlt} label={post.title} className="article__media" />
        <div className="prose">
          {post.body.map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>
        <div className="panel panel--cta">
          <p>Moved by this story? Help us write the next one.</p>
          <Link href="/donate" className="btn btn--accent">
            Donate
          </Link>
        </div>
      </div>
    </article>
  );
}
