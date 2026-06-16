"use client";

import { useState } from "react";
import type { TriageRequest } from "@/lib/types";

const TIERS = ["", "free", "pro", "vip", "enterprise"];
const PRODUCTS = ["", "web", "mobile", "api"];

const SAMPLE: TriageRequest = {
  title: "Production API returning 503 errors",
  body: "Our integration has been failing since this morning. The API is down and returning 503s on every call. This is urgent and impacting our customers.",
  product: "api",
  customer_tier: "enterprise",
};

interface TicketFormProps {
  onSubmit: (payload: TriageRequest) => void;
  loading: boolean;
}

export function TicketForm({ onSubmit, loading }: TicketFormProps) {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [product, setProduct] = useState("");
  const [tier, setTier] = useState("");

  function loadSample() {
    setTitle(SAMPLE.title);
    setBody(SAMPLE.body);
    setProduct(SAMPLE.product ?? "");
    setTier(SAMPLE.customer_tier ?? "");
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    onSubmit({
      title: title.trim(),
      body: body.trim(),
      product: product || undefined,
      customer_tier: tier || undefined,
    });
  }

  const disabled = loading || title.trim().length === 0 || body.trim().length === 0;

  return (
    <form onSubmit={handleSubmit} className="card p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-100">New ticket</h2>
        <button type="button" onClick={loadSample} className="text-xs text-accent-400 hover:text-accent-500">
          Load sample
        </button>
      </div>

      <div className="space-y-4">
        <div>
          <label htmlFor="title" className="field-label">
            Subject
          </label>
          <input
            id="title"
            className="field-input"
            placeholder="Short summary of the issue"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
        </div>

        <div>
          <label htmlFor="body" className="field-label">
            Description
          </label>
          <textarea
            id="body"
            rows={6}
            className="field-input resize-y"
            placeholder="Paste the full ticket body here"
            value={body}
            onChange={(event) => setBody(event.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="product" className="field-label">
              Product
            </label>
            <select
              id="product"
              className="field-input"
              value={product}
              onChange={(event) => setProduct(event.target.value)}
            >
              {PRODUCTS.map((option) => (
                <option key={option} value={option}>
                  {option === "" ? "Not set" : option}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="tier" className="field-label">
              Customer tier
            </label>
            <select
              id="tier"
              className="field-input"
              value={tier}
              onChange={(event) => setTier(event.target.value)}
            >
              {TIERS.map((option) => (
                <option key={option} value={option}>
                  {option === "" ? "Not set" : option}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button type="submit" className="btn-primary w-full" disabled={disabled}>
          {loading ? "Triaging..." : "Triage ticket"}
        </button>
      </div>
    </form>
  );
}
