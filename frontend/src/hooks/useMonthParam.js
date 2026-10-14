import { useSearchParams } from "react-router-dom";
import { currentMonth } from "../lib/format";

const MONTH = /^\d{4}-(0[1-9]|1[0-2])$/;

// The selected month lives in the URL (?month=YYYY-MM) so it survives reloads and links.
export function useMonthParam() {
  const [searchParams, setSearchParams] = useSearchParams();
  const param = searchParams.get("month");
  const month = param && MONTH.test(param) ? param : currentMonth();

  const setMonth = (next) =>
    setSearchParams(
      (params) => {
        params.set("month", next);
        return params;
      },
      { replace: true },
    );

  return [month, setMonth];
}
