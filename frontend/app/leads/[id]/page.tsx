import { LeadDetailClient } from "@/components/lead-detail-client";

export default function LeadDetailPage({ params }: { params: { id: string } }) {
  return <LeadDetailClient id={params.id} />;
}
