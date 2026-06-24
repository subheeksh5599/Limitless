"use client";

import { useEffect } from "react";

const scrollObserver =
  typeof window !== "undefined"
    ? new IntersectionObserver(
        (entries) => entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add("visible"); }),
        { threshold: 0.12 }
      )
    : null;

export default function Home() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    document.querySelectorAll(".reveal, .slide-left, .slide-right, .scale-in").forEach((el) => scrollObserver?.observe(el));
    return () => scrollObserver?.disconnect();
  }, []);

  const H2 = ({ children }: { children: React.ReactNode }) => (
    <h2 className="reveal mb-3.5 font-[family-name:var(--font-newsreader)] text-[clamp(1.7rem,3vw,2.2rem)] font-medium leading-[1.2] tracking-[-0.02em]">
      {children}
    </h2>
  );
  const Lead = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <p className={`reveal mb-11 max-w-[520px] text-[1.05rem] text-muted ${className}`}>{children}</p>
  );

  return (
    <>
      <nav className="mx-auto flex max-w-[960px] items-center justify-between px-6 py-5">
        <a href="/" className="text-[17px] font-semibold tracking-[-0.01em] text-ink no-underline">
          Limit<span className="text-accent">less</span>
        </a>
        <ul className="flex gap-7 list-none">
          {[
            ["#how", "How"],
            ["#why", "Why"],
            ["#stack", "Stack"],
            ["https://github.com/subheeksh5599/Limitless", "GitHub"],
          ].map(([href, label]) => (
            <li key={label}>
              <a href={href} className="text-[14px] text-muted no-underline transition-colors hover:text-ink">{label}</a>
            </li>
          ))}
        </ul>
      </nav>

      {/* HERO */}
      <section className="relative overflow-hidden pb-20 pt-[120px]">
        <div
          className="pointer-events-none fixed right-[-15%] top-[-30%] -z-0 h-[70vw] w-[70vw]"
          style={{
            background: "radial-gradient(circle at 65% 35%, rgba(108,71,199,0.025) 0%, rgba(108,71,199,0.012) 40%, transparent 70%)",
            animation: "ambientPulse 18s ease-in-out infinite alternate",
          }}
        />
        <div className="container mx-auto max-w-[960px] px-6">
          <h1 className="reveal relative z-10 max-w-[680px] font-[family-name:var(--font-newsreader)] text-[clamp(2.4rem,4.8vw,3.4rem)] font-medium leading-[1.1] tracking-[-0.025em]">
            Your agent failed.<br />Read the trace.<br />Fix the skill.<br />Run it again.
          </h1>
          <p className="reveal reveal-delay-1 relative z-10 mt-6 max-w-[540px] text-[1.12rem] leading-relaxed text-muted">
            Limitless wraps GEPA around EvoSkill to give any agent a self-improvement loop. No new model. No benchmark dataset. No RL cluster. Just execution traces, reflection, and targeted edits to skill files.
          </p>
          <a
            href="https://github.com/subheeksh5599/Limitless"
            className="reveal reveal-delay-2 relative z-10 mt-9 inline-flex items-center gap-2.5 rounded-md bg-ink px-7 py-3.5 text-sm font-medium text-white no-underline transition-colors hover:bg-[#2D2D2A] active:scale-[0.98]"
          >
            View on GitHub
          </a>
          <div className="reveal reveal-delay-3 relative z-10 mt-14 flex gap-14 max-sm:flex-wrap max-sm:gap-7">
            {[
              ["100-500", "evaluations per run"],
              ["Apache 2.0", "open source"],
              ["MIT", "GEPA engine"],
            ].map(([num, label]) => (
              <div key={label}>
                <b className="block font-[family-name:var(--font-newsreader)] text-[2rem] font-medium leading-none">{num}</b>
                <span className="text-[13px] uppercase tracking-[0.05em] text-muted">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* THE LOOP */}
      <section id="how" className="py-20">
        <div className="container mx-auto max-w-[960px] px-6">
          <H2>The loop</H2>
          <Lead>A frozen model, an execution trace, and five operations.</Lead>
          <div className="grid grid-cols-[repeat(auto-fit,minmax(280px,1fr))] gap-4">
            {[
              ["Execute", "Run the agent on a task. Capture every tool call, output, error, and retry."],
              ["Reflect", "Pass the trace to a reflection model. It identifies what went wrong — not whether it failed, but why."],
              ["Mutate", "Edit the skill file to address the root cause. One targeted change. Not a rewrite."],
              ["Evaluate", "Run the mutated agent against held-out examples. If the score improves, keep the edit. Otherwise discard."],
              ["Select", "Maintain a fixed-size frontier of best-performing variants. When full, the weakest leaves."],
            ].map(([title, desc], i) => (
              <div key={i} className={`reveal reveal-delay-${i % 4} rounded-lg border border-border bg-surface p-8 transition-colors hover:border-accent`}>
                <div className="mb-3 font-[family-name:var(--font-geist-mono)] text-[12px] uppercase tracking-[0.06em] text-accent">
                  {`0${i + 1}`}
                </div>
                <h3 className="mb-2 text-[1.05rem] font-medium">{title}</h3>
                <p className="text-[14px] leading-relaxed text-muted">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* WHY GEPA */}
      <section id="why" className="py-20">
        <div className="container mx-auto max-w-[960px] px-6">
          <H2>Why reflection beats RL</H2>
          <Lead>
            RL collapses an entire execution into a scalar reward — pass or fail. GEPA reads the trace. The difference in sample efficiency is roughly 35x.
          </Lead>
          <div className="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
            <div className="slide-left reveal rounded-lg border border-border bg-surface p-9">
              <span className="mb-4 inline-block rounded-[3px] bg-[rgba(108,71,199,0.06)] px-2.5 py-1 font-[family-name:var(--font-geist-mono)] text-[11px] uppercase tracking-[0.07em] text-accent">RL / GRPO</span>
              <h3 className="mb-3 text-[1.1rem] font-medium">Sees the score. Not the failure.</h3>
              <p className="text-[14px] leading-relaxed text-muted">
                Collapses execution into 0 or 1. No signal about what went wrong. Requires 5,000 to 25,000 rollouts to converge. Needs GPU clusters.
              </p>
            </div>
            <div className="slide-right reveal rounded-lg border border-border bg-surface p-9">
              <span className="mb-4 inline-block rounded-[3px] bg-[rgba(108,71,199,0.06)] px-2.5 py-1 font-[family-name:var(--font-geist-mono)] text-[11px] uppercase tracking-[0.07em] text-accent">GEPA</span>
              <h3 className="mb-3 text-[1.1rem] font-medium">Reads the whole trace.</h3>
              <p className="text-[14px] leading-relaxed text-muted">
                Error messages, tool outputs, profiler data, reasoning logs. The reflection model diagnoses the specific failure. 100 to 500 evaluations. $2-10 per run. API calls only.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* EXTENSIONS */}
      <section id="stack" className="py-20">
        <div className="container mx-auto max-w-[960px] px-6">
          <H2>What Limitless adds to EvoSkill</H2>
          <Lead>
            EvoSkill discovers skills from failures. Limitless adds continuous improvement, a shareable registry, and cross-agent transfer.
          </Lead>
          <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-4">
            {[
              ["Continuous evolution", "EvoSkill runs as a deliberate command against a benchmark. limitless watch monitors logs and triggers optimization automatically. The agent improves through use."],
              ["Skill registry", "limitless publish sends a skill to a Git repo. limitless install pulls it into any project. Skills compound across the ecosystem instead of dying in .claude/skills/."],
              ["Cross-agent transfer", "Skills include compatibility metadata. An agent starting a task queries the registry for applicable skills. EvoSkill already shows cross-task transfer works (SealQA → BrowseComp, +5.3%)."],
            ].map(([title, desc], i) => (
              <div key={i} className="reveal reveal-delay-1 rounded-lg border border-border bg-surface p-8 transition-colors hover:border-accent">
                <h3 className="mb-2 text-[1.05rem] font-medium">{title}</h3>
                <p className="text-[14px] leading-relaxed text-muted">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* REAL RESULTS */}
      <section className="py-20">
        <div className="container mx-auto max-w-[960px] px-6">
          <H2>Production numbers</H2>
          <Lead>GEPA is already deployed. These are real results from teams using the engine underneath Limitless.</Lead>
          <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4">
            {[
              ["55% → 82%", "Jinja coding tasks, auto-learned agent skills"],
              ["32% → 89%", "ARC-AGI, architecture discovered by GEPA"],
              ["40% savings", "Cloud scheduling policy, beat expert heuristics"],
              ["+37pp NPS", "Nubank customer support agents, 100M users"],
              ["90x cheaper", "Databricks enterprise agents, vs previous approach"],
              ["35x faster", "Convergence speed vs RL/GRPO, ICLR 2026"],
            ].map(([num, desc], i) => (
              <div key={i} className="reveal reveal-delay-1 rounded-lg border border-border p-6">
                <div className="mb-1 font-[family-name:var(--font-newsreader)] text-[1.8rem] font-medium leading-none">{num}</div>
                <div className="text-[13px] leading-relaxed text-muted">{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-[100px] text-center">
        <div className="container mx-auto max-w-[960px] px-6">
          <h2 className="reveal mb-4 font-[family-name:var(--font-newsreader)] text-[clamp(1.7rem,3vw,2.2rem)] font-medium leading-[1.2] tracking-[-0.02em]">
            The model never changes.<br />The agent keeps getting better.
          </h2>
          <p className="reveal mx-auto mb-8 max-w-[460px] text-muted">
            Apache 2.0. Built on GEPA and EvoSkill. Works with any LLM provider.
          </p>
          <a href="https://github.com/subheeksh5599/Limitless" className="reveal inline-flex items-center gap-2.5 rounded-md bg-ink px-7 py-3.5 text-sm font-medium text-white no-underline transition-colors hover:bg-[#2D2D2A] active:scale-[0.98]">
            View on GitHub
          </a>
        </div>
      </section>

      <footer className="border-t border-border py-9 pb-14 text-[13px] text-muted">
        <div className="container mx-auto flex max-w-[960px] flex-wrap items-center justify-between gap-5 px-6">
          <span>Limitless &mdash; Apache 2.0</span>
          <div className="flex gap-6">
            <a href="https://github.com/subheeksh5599/Limitless" className="text-muted no-underline transition-colors hover:text-ink">GitHub</a>
            <a href="https://github.com/sentient-agi/EvoSkill" className="text-muted no-underline transition-colors hover:text-ink">EvoSkill</a>
            <a href="https://github.com/gepa-ai/gepa" className="text-muted no-underline transition-colors hover:text-ink">GEPA</a>
          </div>
        </div>
      </footer>
    </>
  );
}
