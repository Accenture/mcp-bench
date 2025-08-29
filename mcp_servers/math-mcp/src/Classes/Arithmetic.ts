export class Arithmetic {
    /**
     * Add two numbers together
     * @param firstNumber - The first number 
     * @param secondNumber - The second number
     * @returns sum
     */
    static add(firstNumber: number, secondNumber: number): number {
        const sum = firstNumber + secondNumber;
        return sum
    }

    /**
     * Subtract one number from another
     * @param minuend - The number to subtract from
     * @param subtrahend - The number to subtract
     * @returns difference
     */
    static subtract(minuend: number, subtrahend: number) {
        const difference = minuend - subtrahend
        return difference
    }

    /**
     * Multiply two numbers together
     * @param firstNumber - The first number
     * @param secondNumber - The second number
     * @returns product
     */
    static multiply(firstNumber: number, secondNumber: number) {
        const product = firstNumber * secondNumber
        return product
    }

    /**
     * Divide one number by another
     * @param numerator - The number to be divided
     * @param denominator - The number to divide by
     * @returns quotient
     */
    static division(numerator: number, denominator: number) {
        const quotient = numerator / denominator
        return quotient
    }

    /**
     * Calculate the sum of an array of numbers
     * @param numbers - Array of numbers to sum
     * @returns sum of all numbers in the array
     */
    static sum(numbers: number[]) {
        // Use reduce to accumulate the sum, starting with 0
        const sum = numbers.reduce((accumulator, currentValue) => accumulator + currentValue, 0);
        return sum
    }

    /**
     * Calculate the floor of a number
     * @param number - Number to find the floor of
     * @returns floor of the number
     */
    static floor(number: number) {
        const floor = Math.floor(number)
        return floor
    }

    /**
     * Calculate the ceil of a number
     * @param number - Number to find the ceil of
     * @returns ceil of the number
     */
    static ceil(number: number) {
        const ceil = Math.ceil(number)
        return ceil
    }

    /**
     * Calculate the round of a number
     * @param number - Number to find the round of
     * @returns round of the number
     */
    static round(number: number) {
        const round = Math.round(number)
        return round
    }
}
