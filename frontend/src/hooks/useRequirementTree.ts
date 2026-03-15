import { useCallback, useEffect, useState } from 'react';
import { type Iteration, type Product, productsApi, type Requirement } from '@/lib/api';

export function useRequirementTree() {
  const [products, setProducts] = useState<Product[]>([]);
  const [expandedProducts, setExpandedProducts] = useState<Set<string>>(new Set());
  const [iterations, setIterations] = useState<Record<string, Iteration[]>>({});
  const [iterationsLoading, setIterationsLoading] = useState<Record<string, boolean>>({});
  const [expandedIterations, setExpandedIterations] = useState<Set<string>>(new Set());
  const [requirements, setRequirements] = useState<Record<string, Requirement[]>>({});
  const [requirementsLoading, setRequirementsLoading] = useState<Record<string, boolean>>({});
  const [selectedReqId, setSelectedReqId] = useState<string | null>(null);
  const [selectedReqTitle, setSelectedReqTitle] = useState('');

  useEffect(() => {
    productsApi
      .list()
      .then((data) => setProducts(Array.isArray(data) ? data : []))
      .catch(console.error);
  }, []);

  const toggleProduct = useCallback(
    async (productId: string) => {
      setExpandedProducts((prev) => {
        const next = new Set(prev);
        if (next.has(productId)) {
          next.delete(productId);
        } else {
          next.add(productId);
          if (!iterations[productId]) {
            setIterationsLoading((prev) => ({ ...prev, [productId]: true }));
            productsApi
              .listIterations(productId)
              .then((data) =>
                setIterations((p) => ({ ...p, [productId]: Array.isArray(data) ? data : [] })),
              )
              .catch((error) => {
                console.error(error);
                setIterations((p) => ({ ...p, [productId]: [] }));
              })
              .finally(() =>
                setIterationsLoading((prev) => ({
                  ...prev,
                  [productId]: false,
                })),
              );
          }
        }
        return next;
      });
    },
    [iterations],
  );

  const toggleIteration = useCallback(
    async (productId: string, iterationId: string) => {
      setExpandedIterations((prev) => {
        const next = new Set(prev);
        if (next.has(iterationId)) {
          next.delete(iterationId);
        } else {
          next.add(iterationId);
          if (!requirements[iterationId]) {
            setRequirementsLoading((prev) => ({ ...prev, [iterationId]: true }));
            productsApi
              .listRequirements(productId, iterationId)
              .then((data) =>
                setRequirements((p) => ({ ...p, [iterationId]: Array.isArray(data) ? data : [] })),
              )
              .catch((error) => {
                console.error(error);
                setRequirements((p) => ({ ...p, [iterationId]: [] }));
              })
              .finally(() =>
                setRequirementsLoading((prev) => ({
                  ...prev,
                  [iterationId]: false,
                })),
              );
          }
        }
        return next;
      });
    },
    [requirements],
  );

  const selectRequirement = useCallback((req: Requirement) => {
    setSelectedReqId(req.id);
    setSelectedReqTitle(req.title);
  }, []);

  return {
    products,
    expandedProducts,
    iterations,
    iterationsLoading,
    expandedIterations,
    requirements,
    requirementsLoading,
    selectedReqId,
    selectedReqTitle,
    toggleProduct,
    toggleIteration,
    selectRequirement,
  };
}
