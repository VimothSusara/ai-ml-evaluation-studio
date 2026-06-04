import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { CheckCircle2, XCircle } from "lucide-react";
import type { ValidationResponse } from "@/types/api";

export function ValidationPanel({
  validation,
}: {
  validation: ValidationResponse;
}) {
  return (
    <div className="space-y-3">
      <Alert variant={validation.ready_to_train ? "default" : "destructive"}>
        {validation.ready_to_train ? (
          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
        ) : (
          <XCircle className="h-4 w-4" />
        )}
        <AlertTitle>
          {validation.ready_to_train ? "Ready to train" : "Not ready to train"}
        </AlertTitle>
        <AlertDescription className="space-y-1">
          <p>
            Inferred problem:{" "}
            <strong>{validation.inferred_problem_type}</strong>
            {validation.problem_type !== validation.inferred_problem_type && (
              <>
                {" "}
                → using <strong>{validation.problem_type}</strong>
              </>
            )}
          </p>
        </AlertDescription>
      </Alert>

      {[
        ...validation.dataset_validation.errors,
        ...validation.target_validation.errors,
      ].length > 0 && (
        <Alert variant="destructive">
          <AlertTitle>Errors</AlertTitle>
          <AlertDescription>
            <ul className="list-inside list-disc text-sm">
              {[
                ...validation.dataset_validation.errors,
                ...validation.target_validation.errors,
              ].map((e) => (
                <li key={e}>{e}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {[
        ...validation.dataset_validation.warnings,
        ...validation.target_validation.warnings,
      ].length > 0 && (
        <Alert>
          <AlertTitle>Warnings</AlertTitle>
          <AlertDescription>
            <ul className="list-inside list-disc text-sm">
              {[
                ...validation.dataset_validation.warnings,
                ...validation.target_validation.warnings,
              ].map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
