from typing import List, Tuple
import random


def generate_pairs(num) -> List[Tuple[int, int]]:
    """
    Generate pairs of integers from 0 to `num`.

    Args:
        num (int): The upper limit for generating the integers.

    Returns:
        List[Tuple[int, int]]: A list of tuples, each containing a pair
            of integers.

    Raises:
        None.
    """
    lista = [x for x in range(num)]
    listb = [x for x in range(num)]
    result = []

    for x in range(len(lista) - 1):
        random_index = random.randrange(len(listb))
        while lista[x] == listb[random_index]:
            random_index = random.randrange(len(listb))
        result.append((lista[x], listb[random_index]))
        listb.pop(random_index)


    if lista[-1] == listb[0]:
        return generate_pairs(num)
    else:
        result.append((lista[-1], listb[0]))
        return result
