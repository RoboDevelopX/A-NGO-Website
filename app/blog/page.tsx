import type { Metadata } from "next";
import { getPosts } from "@/lib/content";
import { PageHeader } from "@/components/PageHeader";
import { PostCard } from "@/components/Cards";

export const metadata: Metadata = { title: "Blog" };

export default function BlogPage() {
  const posts = getPosts();
  return (
    <>
      <PageHeader eyebrow="Blog" title="Stories from the field" intro="News, updates and the people behind our work." />
      <section className="section">
        <div className="container grid grid--3">
          {posts.map((p) => (
            <PostCard key={p.slug} post={p} />
          ))}
        </div>
      </section>
    </>
  );
}
