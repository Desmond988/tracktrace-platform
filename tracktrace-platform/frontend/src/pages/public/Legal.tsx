import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { api } from "../../lib/api";
import { localized } from "../../lib/localized";

interface LegalPage { slug: string; title: Record<string, string>; body: Record<string, string>; legally_reviewed: boolean; review_note?: Record<string, string> | null; }

// 1. PRIVACY POLICY - EDITED
const PROFESSIONAL_PRIVACY_BODY = `## Who we are
TracksLogistics, based in New York City, New York, United States, is responsible for the personal data described in this policy.

If you have any questions about your privacy, contact us at trackslogistic0@gmail.com or call us at +1 (936) 276-8193.

## What we collect
We collect only the information we need to provide our  Track and logistics services:

- Account details: Your name, email address, and phone number.
- Shipment details: Pickup and delivery addresses, shipment contents, and delivery instructions.
- Messages: Messages you send us through quote forms, contact forms, and customer support.
- Technical data: Basic device and usage information needed to keep the platform secure and working properly.

## How we use it
We use your information to:

- Provide shipment tracking and logistics services.
- Respond to your quote requests, messages, and support inquiries.
- Send shipment notifications you have enabled.
- Improve our services and protect the platform against abuse and fraud.

We do not sell your personal data to third parties.

## How we protect your data
We take reasonable measures to protect your information, including secure storage and restricted access. Your shipment tracking history is stored permanently so you and our team can always see what happened and when.

## Your rights
You may ask us to access, correct, or delete your personal data at any time. To make a request, contact us at trackslogistic0@gmail.com or call +1 (936) 276-8193. We will respond to your request promptly.

## Contact us
TracksLogistics
New York City, New York, United States
Email: trackslogistic0@gmail.com
Phone: +1 (936) 276-8193`;

// 2. TERMS & CONDITIONS - EDITED
const PROFESSIONAL_TERMS_BODY = `## Using this website
By using this website, you agree to these Terms & Conditions. If you do not agree, please do not use the website.

Tracking information is provided for your convenience and reflects the latest event recorded by our team. While we work to keep it accurate and up to date, delivery times may vary due to carrier schedules, customs, weather, and other factors beyond our control.

## Accounts
When you create an account, you are responsible for keeping your password confidential and for all activity under your account.

You agree to provide accurate information and to notify us promptly if you believe your account has been used without your permission.

We may suspend or close an account that violates these terms or is used for fraudulent activity.

## Services
 Track and logistics services are provided by TracksLogistics under the agreement made for each shipment, including the quote, booking confirmation, and any shipping documents for that shipment.

Our services include shipment booking, tracking, customer support, and delivery coordination as described on this website. Specific service details, transit times, and charges will be confirmed for each shipment before booking.

## Quotes and payments
Quotes are provided based on the information you give us. Final charges may change if shipment weight, dimensions, contents, pickup or delivery details differ from the original request.

Payment terms will be confirmed at the time of booking. You agree to pay all applicable charges for services you request.

## Your responsibilities
You are responsible for ensuring that:

- Shipment information you provide is accurate and complete.
- Goods are properly packed and labelled for transport.
- You do not ship prohibited, illegal, or hazardous goods without prior written approval from TracksLogistics.
- All required customs and shipping documents are provided where applicable.

## Liability
TracksLogistics will take reasonable care in handling your shipments. Liability for loss or damage, if any, will be determined under the agreement for each shipment and applicable law.

Nothing in these terms limits liability that cannot be limited by law.

## Changes
We may update these terms from time to time to reflect changes in our services or legal requirements. The date of the latest update will be shown on this page. Continued use of the website after an update means you accept the updated terms.

## Contact us
TracksLogistics
New York City, New York, United States
Email: trackslogistic0@gmail.com
Phone: +1 (936) 276-8193`;

// 3. SHIPPING TERMS - EDITED
const PROFESSIONAL_SHIPPING_BODY = `## Booking and acceptance
Shipments are accepted subject to the details supplied by the sender being accurate and complete, including cargo description, weight, and dimensions.

By booking a shipment with TracksLogistics, you confirm that the information you provided is true and that you are authorized to ship the goods.

We reserve the right to refuse, delay, or return any shipment if the information provided is incomplete, inaccurate, or if the shipment does not comply with these terms or applicable laws.

## Prohibited and restricted goods
The following goods are prohibited or restricted and must not be shipped without prior written approval from TracksLogistics:

- Illegal goods, including narcotics, counterfeit items, and stolen property.
- Hazardous materials, explosives, flammable substances, and toxic chemicals, unless approved and properly declared.
- Perishable goods requiring special handling, unless agreed in advance.
- Live animals, cash, precious metals, and high-value negotiable documents.
- Any goods prohibited by the laws of the origin, transit, or destination country.

If prohibited goods are discovered, TracksLogistics may hold, return, or dispose of the shipment as required by law, and any additional costs will be charged to the sender.

## Packaging and labelling
You are responsible for ensuring your goods are properly packed, sealed, and labelled for safe transport. Packaging must be suitable to protect the contents throughout transit.

TracksLogistics is not responsible for damage caused by inadequate packaging.

## Delivery estimates
Estimated delivery dates are estimates, not guarantees, and may change because of customs, weather, capacity, carrier delays, or other factors outside our control.

Tracking updates reflect the latest event recorded by our team and are provided for your convenience.

## Customs and duties
For international shipments, the sender is responsible for providing accurate customs documentation and for any duties, taxes, or clearance charges, unless otherwise agreed in writing.

Delays caused by customs inspections or missing documents are outside the control of TracksLogistics.

## Delivery and collection
Deliveries will be made to the address provided at booking. If the recipient is unavailable, we will attempt delivery or arrange collection as agreed for that shipment.

Additional storage or re-delivery charges may apply if delivery cannot be completed due to incorrect address details or recipient unavailability.

## Contact us
TracksLogistics
New York City, New York, United States
Email: trackslogistic0@gmail.com
Phone: +1 (936) 276-8193`;

// 4. CARGO LIABILITY - EDITED
const PROFESSIONAL_CARGO_BODY = `## Liability
The limits and conditions of liability for loss or damage to cargo depend on the mode of transport and the applicable law or convention.

TracksLogistics will take reasonable care in handling your cargo from pickup to delivery. Where loss or damage occurs, liability will be determined under the agreement made for that shipment, including the quote, booking confirmation, and any shipping documents, and under the applicable law for that mode of transport.

Liability does not apply to loss or damage caused by:

- Inadequate or improper packaging by the sender.
- Inaccurate or incomplete shipment information provided by the sender.
- Prohibited, undeclared, or improperly declared goods.
- Acts of God, war, civil unrest, customs seizure, or other events beyond our reasonable control.
- Normal wear, inherent defects, or the natural properties of the goods.

Nothing in this policy limits liability that cannot be limited by law.

## Claims
Report loss or damage as soon as possible and keep the packaging and photographs.

To file a claim, please contact us within 7 days of delivery, or within 7 days of the expected delivery date if your shipment has not arrived. Please include:

- Your tracking number and shipment details.
- Photographs of the packaging and the damaged goods.
- A description of the loss or damage.
- Any supporting documents, such as invoices or proof of value.

We will review your claim promptly and contact you with the next steps. To avoid delays, please keep all original packaging until your claim is resolved.

## Contact us
TracksLogistics
New York City, New York, United States
Email: trackslogistic0@gmail.com
Phone: +1 (936) 276-8193`;

// 5. DATA PROTECTION - EDITED
const PROFESSIONAL_DATA_PROTECTION_BODY = `## Security
We take the security of your personal data seriously.

Passwords are stored using a one-way hash. Access to shipment data is limited to the customer it belongs to and authorised staff who need it to provide our services.

We use reasonable technical and organisational measures to protect your data against unauthorised access, loss, or misuse.

## Retention
We keep your data only for as long as we need it to provide our services and meet our legal obligations.

- Shipment data: Kept permanently so you and our team can always see your full tracking history.
- Account data: Kept while your account is active, and for a reasonable period afterwards to handle any follow-up requests.
- Messages: Kept for as long as needed to respond to your inquiry and maintain a record of our communication.

When data is no longer needed, it will be securely deleted or anonymised.

## Your rights
You have the right to:

- Request a copy of the personal data we hold about you.
- Ask us to correct inaccurate data.
- Ask us to delete your data, where permitted by law.
- Ask us to limit how we use your data.
- Object to certain uses of your data.

## Requests and complaints
To exercise your data rights, contact us at trackslogistic0@gmail.com or call us at +1 (936) 276-8193. We will respond to your request promptly.

If you are not satisfied with our response, you may contact the applicable data protection authority in your jurisdiction.

## Contact us
TracksLogistics
New York City, New York, United States
Email: trackslogistic0@gmail.com
Phone: +1 (936) 276-8193`;

// 7. ACCESSIBILITY - EDITED
const PROFESSIONAL_ACCESSIBILITY_BODY = `## Our aim
We want this website to be usable by everyone, including people using keyboards and screen readers.

We work to make our website clear, easy to navigate, and accessible across devices. This includes readable text, clear headings, keyboard navigation, and labels for key actions such as tracking a shipment, requesting a quote, and contacting us.

## If you find a barrier
If you find a barrier on this website, please tell us at trackslogistic0@gmail.com or call us at +1 (936) 276-8193, and we will work with you to fix it.

When you contact us, please tell us:

- The page where you had difficulty.
- What you were trying to do.
- The device or assistive technology you were using, if you are comfortable sharing it.

We will do our best to provide the information you need in an alternative format and to resolve the issue promptly.

## Status
TracksLogistics is committed to improving the accessibility of this website on an ongoing basis. We regularly review our website and work to address accessibility issues as they are identified.

## Contact us
TracksLogistics
New York City, New York, United States
Email: trackslogistic0@gmail.com
Phone: +1 (936) 276-8193`;

// 6. COOKIE POLICY - KEEP AS IS - NO CODE HERE
// 8. DISCLAIMER - KEEP AS IS - NO CODE HERE

export default function Legal() {
  const { slug } = useParams();
  const { i18n } = useTranslation();
  const [page, setPage] = useState<LegalPage | null>(null);

  useEffect(() => { api.get<LegalPage>(`/api/legal/${slug}`).then(setPage).catch(() => setPage(null)); }, [slug]);
  if (!page) return null;
  const title = localized(page.title, i18n.language);
  let body = localized(page.body, i18n.language);

  const isPrivacy = slug === "privacy-policy" || slug === "privacy";
  const isTerms = slug === "terms" || slug === "terms-and-conditions" || slug === "terms-conditions";
  const isShipping = slug === "shipping-terms" || slug === "shipping" || slug === "shipping-policy";
  const isCargo = slug === "cargo-liability" || slug === "cargo" || slug === "liability";
  const isDataProtection = slug === "data-protection" || slug === "data";
  const isAccessibility = slug === "accessibility";
  // Cookie + Disclaimer intentionally NOT replaced

  if (isPrivacy && (body.includes(" trackslogistic0@gmail.com") || body.includes("placeholder") || body.includes("not been reviewed") || body.includes(" TrackXpress"))) {
    body = PROFESSIONAL_PRIVACY_BODY;
  }
  if (isTerms && (body.includes("[COMPANY") || body.includes("placeholder") || body.includes("not been reviewed") || body.includes(" TrackXpress"))) {
    body = PROFESSIONAL_TERMS_BODY;
  }
  if (isShipping && (body.includes("will publish") || body.includes("[COMPANY") || body.includes("placeholder") || body.includes("not been reviewed") || body.includes(" TrackXpress"))) {
    body = PROFESSIONAL_SHIPPING_BODY;
  }
  if (isCargo && (body.includes("will state") || body.includes("[COMPANY") || body.includes("placeholder") || body.includes("not been reviewed") || body.includes(" TrackXpress"))) {
    body = PROFESSIONAL_CARGO_BODY;
  }
  if (isDataProtection && (body.includes("[COMPANY") || body.includes("[DATA") || body.includes("will state") || body.includes("placeholder") || body.includes("not been reviewed") || body.includes(" TrackXpress"))) {
    body = PROFESSIONAL_DATA_PROTECTION_BODY;
  }
  if (isAccessibility && (body.includes("[COMPANY") || body.includes("will be added") || body.includes("placeholder") || body.includes("not been reviewed") || body.includes(" TrackXpress"))) {
    body = PROFESSIONAL_ACCESSIBILITY_BODY;
  }

  return (
    <div className="container" style={{ padding: "48px 0", maxWidth: 680 }}>
      <h1 style={{ fontSize: "1.6rem" }}>{title}</h1>
      <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.7, color: "var(--slate-500)" }}>
        {body.split("\n").map((line, i) => (line.startsWith("## ") ? <h2 key={i} style={{ fontSize: "1.1rem", marginTop: 20, color: "var(--ink-900)" }}>{line.slice(3)}</h2> : line.startsWith("- ") ? <p key={i} style={{ paddingLeft: 12, margin: "4px 0" }}>{line}</p> : <p key={i}>{line}</p>))}
      </div>
      <div style={{ marginTop: 32, paddingTop: 20, borderTop: "1px solid var(--line-200)", fontSize: "0.9rem", color: "var(--slate-500)" }}>
        Questions? Contact us at trackslogistic0@gmail.com or +1 (936) 276-8193
      </div>
    </div>
  );
}