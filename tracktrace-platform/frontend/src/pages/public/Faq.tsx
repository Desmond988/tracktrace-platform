import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../lib/api";
import { localized } from "../../lib/localized";
import ScrollReveal from "../../components/ScrollReveal";
import Accordion, { type AccordionEntry } from "../../components/Accordion";

interface FaqItem { id: string; question: Record<string, string>; answer: Record<string, string>; }

export default function Faq() {
  const { i18n } = useTranslation();
  const [items, setItems] = useState<FaqItem[]>([]);
  useEffect(() => { api.get<FaqItem[]>("/api/faq").then(setItems); }, []);

  const entries: AccordionEntry[] = items.map((f) => ({
    id: f.id,
    question: localized(f.question, i18n.language),
    answer: localized(f.answer, i18n.language),
  }));

  return (
    <div className="container" style={{ padding: "48px 0", maxWidth: 680 }}>
      <h1 style={{ fontSize: "1.8rem" }}>FAQ</h1>
      <ScrollReveal>
        <Accordion items={entries} />
      </ScrollReveal>
    </div>
  );
}
