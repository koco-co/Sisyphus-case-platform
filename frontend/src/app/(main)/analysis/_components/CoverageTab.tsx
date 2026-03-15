'use client';

import { CoverageMatrix } from '../../diagnosis/_components/CoverageMatrix';

interface CoverageTabProps {
  requirementId: string | null;
  visible: boolean;
}

export default function CoverageTab({ requirementId, visible }: CoverageTabProps) {
  if (!requirementId || !visible) return null;
  return <CoverageMatrix reqId={requirementId} />;
}
