import { useState, type ReactNode } from "react";

export interface AccordionEntry {
  id: string;
  question: ReactNode;
  answer: ReactNode;
}

/** Accessible accordion: real <button> triggers with aria-expanded/aria-controls, smooth
 * height animation via CSS grid-rows (see .accordion-panel in tokens.css), keyboard-operable
 * (native button semantics - Enter/Space toggle, Tab moves between triggers). */
export default function Accordion({ items }: { items: AccordionEntry[] }) {
  const [openId, setOpenId] = useState<string | null>(items[0]?.id ?? null);
  return (
    <div>
      {items.map((item) => {
        const open = openId === item.id;
        const panelId = `accordion-panel-${item.id}`;
        const triggerId = `accordion-trigger-${item.id}`;
        return (
          <div className="accordion-item" key={item.id}>
            <h3 style={{ margin: 0 }}>
              <button
                id={triggerId}
                className="accordion-trigger"
                aria-expanded={open}
                aria-controls={panelId}
                onClick={() => setOpenId(open ? null : item.id)}
              >
                <span>{item.question}</span>
                <svg className="accordion-chevron" width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                  <path d="M5 8l5 5 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </h3>
            <div id={panelId} role="region" aria-labelledby={triggerId} className="accordion-panel" data-open={open}>
              <div className="accordion-panel-inner">
                <p>{item.answer}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
